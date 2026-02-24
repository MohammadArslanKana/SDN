import torch.nn as nn
import torch.nn.functional as F

class SDN_CNN(nn.Module):
    def __init__(self, num_features, num_classes, embedding_dim=128):
        super(SDN_CNN, self).__init__()
        
        self.conv1 = nn.Conv1d(num_features, 64, kernel_size=2)
        self.bn1 = nn.BatchNorm1d(64)
        
        self.conv2 = nn.Conv1d(64, 128, kernel_size=1)
        self.bn2 = nn.BatchNorm1d(128)
        
        self.global_pool = nn.AdaptiveAvgPool1d(1)
        
        self.embedding_layer = nn.Linear(128, embedding_dim)
        
        self.classifier = nn.Linear(embedding_dim, num_classes)
        self.binary_head = nn.Linear(embedding_dim, 1)

    def forward(self, x):
        x = F.gelu(self.bn1(self.conv1(x)))
        x = F.gelu(self.bn2(self.conv2(x)))
        
        x = self.global_pool(x).squeeze(-1)
        
        embedding = self.embedding_layer(x)
        
        multi_logits = self.classifier(embedding)
        binary_logits = self.binary_head(embedding)
        
        return binary_logits, multi_logits, embedding
