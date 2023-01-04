import torch.nn as nn
from dgl.nn import GraphConv
import torch.nn.functional as F
import torch


class GraphClassificationModelCrossEntropy(nn.Module):
    def __init__(self, in_dim, hidden_dim, out_dim):
        super(GraphClassificationModelCrossEntropy, self).__init__()
        self.conv1 = GraphConv(in_dim, hidden_dim, allow_zero_in_degree=True)
        self.conv2 = GraphConv(hidden_dim, out_dim, allow_zero_in_degree=True)

    def forward(self, g, features):
        h = self.conv1(g, features)
        h = F.relu(h)
        h = self.conv2(g, h)
        return h

    def fit(self, epochs, graph, optimizer):
        train_mask = graph.ndata['train_mask']
        val_mask = graph.ndata['val_mask']
        labels = graph.ndata['label']
        features = graph.ndata['feat'].float()
        for epoch in range(epochs):
            logits = self(graph, features)
            loss = F.cross_entropy(logits[train_mask], labels[train_mask])
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            if epoch % 10 == 0:
                # Evaluation loop
                with torch.no_grad():
                    logits = self(graph, features)
                    train_acc = (logits[train_mask].argmax(1) == labels[train_mask]).float().mean().item()
                    val_acc = (logits[val_mask].argmax(1) == labels[val_mask]).float().mean().item()
                    print(f'Epoch {epoch}: loss={loss:.4f}, train_acc={train_acc:.4f}, val_acc={val_acc:.4f}')


class GraphClassificationModelBinaryCrossEntropy(nn.Module):
    def __init__(self, in_dim, hidden_dim, out_dim):
        super(GraphClassificationModelBinaryCrossEntropy, self).__init__()
        self.conv1 = GraphConv(in_dim, hidden_dim, allow_zero_in_degree=True)
        #self.conv2 = GraphConv(hidden_dim, hidden_dim, allow_zero_in_degree=True)
        self.conv3 = GraphConv(hidden_dim, out_dim, allow_zero_in_degree=True)

    def forward(self, g, features):
        h = self.conv1(g, features)
        h = F.relu(h)
        #h = self.conv2(g, h)
        h = self.conv3(g, h)
        return h

    def fit(self, epochs, graph, optimizer):
        train_mask = graph.ndata['train_mask']
        val_mask = graph.ndata['val_mask']
        labels = graph.ndata['label']
        features = graph.ndata['feat'].float()
        for epoch in range(epochs):
            logits = self(graph, features)
            loss = F.binary_cross_entropy_with_logits(logits[train_mask], labels[train_mask].float(), pos_weight=torch.tensor([10]))
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            if epoch % 1 == 0:
                # Evaluation loop
                with torch.no_grad():
                    logits = self(graph, features)
                    train_acc_matches = []
                    for id, index in enumerate(torch.max(logits[train_mask], dim=1)[1]):
                        if labels[train_mask][id][index] == 1:
                            train_acc_matches.append(1)
                        else:
                            train_acc_matches.append(0)
                    train_acc = sum(train_acc_matches) / len(train_acc_matches)

                    val_acc_matches = []
                    for id, index in enumerate(torch.max(logits[val_mask], dim=1)[1]):
                        if labels[val_mask][id][index] == 1:
                            val_acc_matches.append(1)
                        else:
                            val_acc_matches.append(0)
                    val_acc = sum(val_acc_matches) / len(val_acc_matches)

                    print(f'Epoch {epoch}: loss={loss:.4f}, train_acc={train_acc:.4f}, val_acc={val_acc:.4f}')


