import torch.nn as nn
import timm

class Model(nn.Module):
    def __init__(self, classes, model='tf_efficientnetv2_s.in21k_ft_in1k'):
        super(Model, self).__init__()
        self._classes = classes
        self._num_classes=len(classes)
        self.model = timm.create_model(model, pretrained=True,num_classes=self.num_classes)
        
        for param in self.model.parameters():
            param.requires_grad = False
        for param in self.model.get_classifier().parameters():
            param.requires_grad = True
    @property
    def classifier(self):
        return self.model.get_classifier()
    @property
    def num_classes(self):
        return self._num_classes
    @property
    def classes(self):
        return self._classes
    #오버라이딩
    def forward(self, x):
        return self.model(x)
