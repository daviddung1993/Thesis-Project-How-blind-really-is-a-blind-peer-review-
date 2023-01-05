import torch
from dgl.data import DGLDataset
import dgl
import numpy as np


class PaperDataset(DGLDataset):
    def __init__(self, nodes_data, edges_data, val_index, training_set_index, one_hot_encoded=False):
        self.nodes_data = nodes_data
        self.edges_data = edges_data
        self.val_index = val_index
        self.one_hot_encoded = one_hot_encoded
        self.training_set_index = training_set_index
        super().__init__(name='paper_dataset')

    def process(self):

        if self.one_hot_encoded:
            total_authors_len = len(self.nodes_data["AuthorID"].unique())
            feature_vector = []
            for idx, paperID in enumerate(self.nodes_data["PaperID"].unique()):
                if idx % 1000 == 0:
                    print(idx)
                author_list = np.zeros(total_authors_len, dtype=np.int32)
                for a in self.nodes_data[self.nodes_data["PaperID"] == paperID].iterrows():
                    author_list[a[1]["AuthorID"]] = 1
                feature_vector.append(author_list)
            node_labels = torch.tensor(feature_vector, dtype=torch.int32)
        else:
            node_labels = torch.from_numpy(self.nodes_data["AuthorID"].to_numpy())
        #node_features = torch.zeros(len(node_labels), 1)
        node_features = node_labels
        #node_features[:self.training_set_index] = torch.zeros(self.training_set_index, node_labels.shape[1])

        edges_src = torch.from_numpy(self.edges_data['ReferenceID'].astype(int).to_numpy())
        edges_dst = torch.from_numpy(self.edges_data['PaperID'].astype(int).to_numpy())

        self.graph = dgl.graph((edges_src, edges_dst), num_nodes=len(node_labels))
        self.graph.ndata['feat'] = node_features
        self.graph.ndata['label'] = node_labels

        n_nodes = len(node_labels)
        val_mask = torch.zeros(n_nodes, dtype=torch.bool)
        test_mask = torch.zeros(n_nodes, dtype=torch.bool)

        for val_in in self.val_index:
            val_mask[int(val_in)] = True
            node_features[int(val_in)] = torch.zeros(node_labels.shape[1])

        #train_mask = torch.zeros(n_nodes, dtype=torch.bool)
        train_mask = np.invert(val_mask).type(torch.bool)
        train_mask[self.training_set_index:] = False

        self.graph.ndata['train_mask'] = train_mask
        self.graph.ndata['val_mask'] = val_mask
        self.graph.ndata['test_mask'] = test_mask

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


