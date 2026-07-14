import torch.nn as nn
import timm

class Model(nn.Module):
    def __init__(self, num_classes, model='tf_efficientnetv2_s.in21k_ft_in1k'):
        super(Model, self).__init__()
        self._num_classes=num_classes
        self.model = timm.create_model(model, pretrained=True,num_classes=num_classes)
        
        for param in self.model.parameters():
            param.requires_grad = False
        for param in self.model.get_classifier().parameters():
            param.requires_grad = True
        self.head=self.model.get_classifier()
    @property
    def num_classes(self):
        return self._num_classes
    #오버라이딩
    def forward(self, x):
        return self.model(x)
