import torch.nn as nn
from torchvision import models

class Model(nn.Module):
    def __init__(self, num_classes):
        super(Model, self).__init__()
        self.model = models.efficientnet_v2_s(weights='DEFAULT')
        
        #Backbone 가중치 고정
        for param in self.model.parameters():
            param.requires_grad = False

        in_features = self.model.classifier[-1].in_features
        self.model.classifier[-1] = nn.Linear(in_features, num_classes)
        self.head = self.model.classifier[-1]

    #오버라이딩
    def forward(self, x):
        return self.model(x)
