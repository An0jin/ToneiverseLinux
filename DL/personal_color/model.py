"""
퍼스널컬러(Personal Color) 진단 및 분류를 위한 전이학습(Transfer Learning) 딥러닝 모델 모듈.

이 모듈은 `train.ipynb`의 학습 및 검증 파이프라인에서 호출되어 사용됩니다.
timm(PyTorch Image Models) 라이브러리의 사전학습(Pretrained) EfficientNetV2 백본을 기반으로 하며,
특성 추출기(Backbone)는 고정(Freeze)하고 최종 분류기(Classifier Head)만 미세조정(Fine-Tuning)하는 전이학습 전략을 구현합니다.
"""

from typing import List
import torch
import torch.nn as nn
import timm
import torchvision
from timm.data.constants import IMAGENET_DEFAULT_MEAN, IMAGENET_DEFAULT_STD


class Model(nn.Module):
    """
    퍼스널컬러 이미지 분류를 위한 전이학습(Transfer Learning) 모델 클래스.

    주요 특징:
    1. Pretrained Backbone:
       - timm의 'tf_efficientnetv2_s.in21k_ft_in1k' 모델을 기본 백본으로 채택.
       - ImageNet-21k에서 사전 학습 후 1k로 미세 조정되어 이미지 특징 추출 능력이 뛰어남.
    2. Feature Extractor Freezing (동결):
       - 백본의 모든 레이어 파라미터를 freeze(`requires_grad = False`)하여
         사전 학습된 고수준의 시각적 특징(Edge, Texture 등) 표현력을 보존하고 연산량을 대폭 절감.
    3. Classifier Head Unfreezing (분류기 학습):
       - 최종 출력 계층(Classifier)만 unfreeze(`requires_grad = True`)하여
         사용자 정의 퍼스널컬러 클래스(예: 봄웜, 여름쿨, 가을웜, 겨울쿨 등)에 맞게 가중치를 학습.
    4. train.ipynb 연계:
       - 옵티마이저 등록: `model.classifier.parameters()`를 통해 AdamW에 학습 대상 파라미터만 전달.
       - 메트릭 초기화: `model.num_classes`를 통해 Accuracy, F1Score 등의 다중 클래스 평가 지표 생성.
       - 클래스 라벨 저장: `model.classes`를 통해 `classes.txt` 생성.
       - ONNX 변환: `forward`를 통해 표준 텐서 입출력을 지원하여 `torch.onnx.export`와 완벽 호환.
    """

    def __init__(self, classes: List[str], model: str = 'tf_efficientnetv2_s.in21k_ft_in1k'):
        """
        Model 클래스 생성자.

        :param classes: 분류할 타깃 클래스 이름의 리스트 (예: image_datasets['train'].classes)
        :param model: timm에서 로드할 사전학습 백본 아키텍처 식별자 문자열
                      (기본값: 'tf_efficientnetv2_s.in21k_ft_in1k')
        """
        super(Model, self).__init__()
        
        # 클래스 목록 및 전체 클래스 개수 저장
        self._classes = classes
        self._num_classes = len(classes)
        
        # 1. timm을 통해 사전학습 가중치가 포함된 모델 생성
        #    - pretrained=True: ImageNet 사전학습 가중치 자동 다운로드 및 로드
        #    - num_classes=self.num_classes: 최종 분류기(FC 레이어) 출력 뉴런 수를 퍼스널컬러 클래스 수로 교체
        self.model = timm.create_model(model, pretrained=True, num_classes=self.num_classes)
        
        # 2. 특성 추출기(Backbone) 파라미터 동결 (Freeze)
        #    - 백본의 모든 파라미터의 gradient 계산을 비활성화하여 역전파(Backpropagation) 시 가중치 갱신 방지
        for param in self.model.parameters():
            param.requires_grad = False
            
        # 3. 최종 분류기(Classifier Head) 레이어 파라미터 활성화 (Unfreeze)
        #    - 교체된 최종 분류기만 학습 대상이 되도록 requires_grad를 True로 설정
        for param in self.model.get_classifier().parameters():
            param.requires_grad = True

        # 4. 입력 이미지 표준화 정규화 (Normalization) 레이어 등록
        #    - timm 사전학습 모델의 입력 기대 분포에 맞춰 ImageNet 통계치(RGB 평균 및 표준편차)로 텐서 정규화
        self.normalize = torchvision.transforms.Normalize(
            mean=IMAGENET_DEFAULT_MEAN,
            std=IMAGENET_DEFAULT_STD
        )

    @property
    def classifier(self) -> nn.Module:
        """
        최종 분류기(Classifier Head) 모듈 반환.
        
        `train.ipynb`의 옵티마이저 정의 시 사용:
        >>> optimizer = AdamW(model.classifier.parameters(), lr=LR)
        동결된 백본 파라미터를 제외하고 실제 학습할 파라미터만 옵티마이저에 전달합니다.
        """
        return self.model.get_classifier()

    @property
    def num_classes(self) -> int:
        """
        분류 대상 클래스의 총 개수(Integer) 반환.
        
        `train.ipynb`의 다중 클래스 평가 지표(MetricCollection) 정의 시 사용:
        >>> Accuracy(task='multiclass', num_classes=model.num_classes)
        """
        return self._num_classes

    @property
    def classes(self) -> List[str]:
        """
        분류 대상 클래스 이름 리스트 반환.
        
        `train.ipynb`에서 학습 완료 후 클래스 메타데이터 파일(`classes.txt`)을 생성할 때 사용:
        >>> file.write("\\n".join(model.classes))
        """
        return self._classes

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        순전파(Forward Pass) 연산 수행.

        입력 이미지 텐서 `x`를 백본과 분류기에 통과시켜 클래스별 비정규화 점수(Logits)를 계산합니다.
        
        :param x: 배치 이미지 텐서 [배치 크기(B), 채널 수(C=3), 높이(H=384), 너비(W=384)]
                  (`train.ipynb`의 IMGZ=(384, 384) 및 ToTensor/Normalize 적용 텐서)
        :return: 각 클래스에 대한 로짓(Logits) 텐서 [배치 크기(B), 클래스 수(Num_Classes)]
                 학습 시 `CrossEntropyLoss`로 직접 전달되어 손실을 계산하고,
                 추론 시 `torch.argmax(outputs, dim=1)`로 최적의 클래스를 예측합니다.
        """
        x = self.normalize(x)
        return self.model(x)

