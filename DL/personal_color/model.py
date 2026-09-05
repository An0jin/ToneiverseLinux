import torch.nn as nn
import timm

class Model(nn.Module):
    """
    퍼스널컬러 이미지 분류를 위한 전이학습(Transfer Learning) 모델
    - timm의 사전학습(Pretrained) EfficientNetV2 백본을 사용
    - 특성 추출기(Backbone)는 가중치를 동결(Freeze)하고, 최종 분류기(Classifier Head)만 학습
    """
    def __init__(self, classes, model='tf_efficientnetv2_s.in21k_ft_in1k'):
        """
        모델 초기화 함수
        :param classes: 분류 대상 클래스 리스트 (예: 봄웜, 여름쿨 등)
        :param model: 사용할 사전학습 모델 구조 이름 (기본값: tf_efficientnetv2_s.in21k_ft_in1k)
        """
        super(Model, self).__init__()
        self._classes = classes
        self._num_classes = len(classes)
        # 1. 사전 학습 가중치를 포함한 모델 생성 및 출력 클래스 수 설정
        self.model = timm.create_model(model, pretrained=True, num_classes=self.num_classes)
        
        # 2. 백본(특성 추출기) 파라미터는 가중치 갱신을 하지 않도록 고정 (Freeze)
        for param in self.model.parameters():
            param.requires_grad = False
            
        # 3. 최종 분류기(Classifier) 레이어의 파라미터만 학습 가능하도록 설정 (Unfreeze)
        for param in self.model.get_classifier().parameters():
            param.requires_grad = True

    @property
    def classifier(self):
        """옵티마이저(Optimizer) 등록에 사용할 최종 분류기 계층 반환"""
        return self.model.get_classifier()

    @property
    def num_classes(self):
        """분류 대상 총 클래스 개수 반환"""
        return self._num_classes

    @property
    def classes(self):
        """클래스 이름 목록 반환"""
        return self._classes

    # 순전파(Forward) 연산 오버라이딩
    def forward(self, x):
        """입력 이미지 텐서 x를 모델에 전달하여 각 클래스별 로짓(Logits) 출력"""
        return self.model(x)

