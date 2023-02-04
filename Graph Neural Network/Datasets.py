import torch
from dgl.data import DGLDataset
import dgl
import numpy as np
import pandas as pd


class PaperDataset(DGLDataset):
    def __init__(self, paper_data, references_data, label_size=0, val=False, one_hot_encoded=False):
        self.paper_data = paper_data.copy()
        self.references_data = references_data.copy()
        self.one_hot_encoded = one_hot_encoded
        self.label_size = label_size
        self.is_val_set = val
        super().__init__(name='paper_dataset')

    def process(self):

        # Remap Ids for DGL so max(nodeID) < len(Nodes)
        unique_paperIds = self.paper_data["PaperID"].unique()
        all_papers_remap_ids = {unique_paperIds[x]: x for x in range(0, len(unique_paperIds))}
        self.paper_data["PaperID"] = self.paper_data["PaperID"].apply(lambda x: all_papers_remap_ids[x])
        self.references_data = self.references_data.applymap(lambda x: all_papers_remap_ids[x])
        train_mask = torch.tensor(pd.Series(list(range(0, len(unique_paperIds)))).isin(self.references_data["PaperID"].to_list()).values)

        # One hot encoding
        if self.one_hot_encoded:
            if self.label_size:
                total_authors_len = self.label_size
            else:
                total_authors_len = len(self.paper_data["AuthorID"].unique())

            feature_vector = []
            for idx, paperID in enumerate(self.paper_data["PaperID"].unique()):
                if idx % 1000 == 0:
                    print(idx)
                author_list = np.zeros(total_authors_len, dtype=np.int32)
                for a in self.paper_data[self.paper_data["PaperID"] == paperID].iterrows():
                    author_list[a[1]["AuthorID"]] = 1
                feature_vector.append(author_list)
            node_labels = torch.tensor(feature_vector, dtype=torch.int32)
        else:
            node_labels = torch.from_numpy(self.paper_data["AuthorID"].to_numpy())
        #node_features = torch.zeros(len(node_labels), 1)
        node_features = node_labels.detach().clone()
        #node_features[:self.training_set_index] = torch.zeros(self.training_set_index, node_labels.shape[1])

        edges_src = torch.from_numpy(self.references_data['ReferenceID'].astype(int).to_numpy())
        edges_dst = torch.from_numpy(self.references_data['PaperID'].astype(int).to_numpy())


        self.graph = dgl.graph((edges_src, edges_dst), num_nodes=len(node_labels))
        #self.graph.ndata["val_index"] = torch.tensor(self.val_index)
        self.graph.ndata['feat'] = node_features
        print(node_features)
        if self.is_val_set:
            #print(self.graph.ndata['feat'][train_mask])
            self.graph.ndata['feat'][train_mask] = 0

        self.graph.ndata['label'] = node_labels

        n_nodes = len(node_labels)
        val_mask = torch.zeros(n_nodes, dtype=torch.bool)
        test_mask = torch.zeros(n_nodes, dtype=torch.bool)

        #train_mask = np.invert(val_mask).type(torch.bool)
        #train_mask[self.training_set_index:] = False

        self.graph.ndata['train_mask'] = train_mask
        #self.graph.ndata['val_mask'] = val_mask
        #self.graph.ndata['test_mask'] = test_mask

    def __getitem__(self, i):
        return self.graph

    def __len__(self):
        return 1


class AuthorDataset(DGLDataset):
    def __init__(self, nodes_data, edges_data):
        self.nodes_data = nodes_data
        self.edges_data = edges_data
        super().__init__(name='author_dataset')

    def process(self):
        # node_features = torch.from_numpy(self.nodes_data['Year'].to_numpy())
        node_features = torch.from_numpy(np.zeros((len(self.nodes_data), 1)))
        node_labels = torch.from_numpy(self.nodes_data['AuthorID'].astype('category').cat.codes.to_numpy())
        edge_features = torch.from_numpy(self.edges_data['Count'].to_numpy()).type(torch.int32)
        edges_src = torch.from_numpy(self.edges_data['RefAuthor'].astype(int).to_numpy())
        edges_dst = torch.from_numpy(self.edges_data['Author'].astype(int).to_numpy())

        self.graph = dgl.graph((edges_src, edges_dst), num_nodes=self.nodes_data.shape[0])
        self.graph.ndata['feat'] = node_features
        self.graph.ndata['label'] = node_labels
        self.graph.edata['weight'] = edge_features

        n_nodes = self.nodes_data.shape[0]
        n_train = int(n_nodes * 0.6)
        n_val = int(n_nodes * 0.2)
        train_mask = torch.zeros(n_nodes, dtype=torch.bool)
        val_mask = torch.zeros(n_nodes, dtype=torch.bool)
        test_mask = torch.zeros(n_nodes, dtype=torch.bool)
        train_mask[:n_train] = True
        val_mask[n_train:n_train + n_val] = True
        test_mask[n_train + n_val:] = True
        self.graph.ndata['train_mask'] = train_mask
        self.graph.ndata['val_mask'] = val_mask
        self.graph.ndata['test_mask'] = test_mask

    def __getitem__(self, i):
        return self.graph

    def __len__(self):
        return 1


class PaperDataset2(DGLDataset):
    def __init__(self, nodes_data, edges_data):
        super().__init__(name='paper_dataset')
        self.nodes_data = nodes_data
        self.edges_data = edges_data

    def process(self):
        node_features = torch.from_numpy(self.nodes_data['Year'].to_numpy())
        node_labels = torch.from_numpy(self.nodes_data['PaperID'].astype('category').cat.codes.to_numpy())
        edge_features = torch.from_numpy(self.edges_data['Weight'].to_numpy())
        edges_src = torch.from_numpy(self.edges_data['Src'].to_numpy())
        edges_dst = torch.from_numpy(self.edges_data['Dst'].to_numpy())

        self.graph = dgl.graph((edges_src, edges_dst), num_nodes=self.nodes_data.shape[0])
        self.graph.ndata['feat'] = node_features
        self.graph.ndata['label'] = node_labels
        self.graph.edata['weight'] = edge_features

        # If your dataset is a node classification dataset, you will need to assign
        # masks indicating whether a node belongs to training, validation, and test set.
        n_nodes = self.nodes_data.shape[0]
        n_train = int(n_nodes * 0.6)
        n_val = int(n_nodes * 0.2)
        train_mask = torch.zeros(n_nodes, dtype=torch.bool)
        val_mask = torch.zeros(n_nodes, dtype=torch.bool)
        test_mask = torch.zeros(n_nodes, dtype=torch.bool)

        val_mask[n_train:n_train + n_val] = True
        # test_mask[n_train + n_val:] = True
        self.graph.ndata['train_mask'] = train_mask
        self.graph.ndata['val_mask'] = val_mask
        # self.graph.ndata['test_mask'] = test_mask

    def __getitem__(self, i):
        return self.graph

    def __len__(self):
        return 1


