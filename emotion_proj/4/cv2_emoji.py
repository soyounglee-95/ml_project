import cv2
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader
import numpy as np 
from torchvision import models


device = torch.device('mps:0' if torch.backends.mps.is_available() else 'cpu')

#Hyper parameter 설정 
BATCH_SIZE = 32
EPOCHS = 20
LEARNING_RATE = 1e-3

def load_emoji():
    smile_emoji = cv2.imread('/Users/soyoung/ml_project/emotion_proj/4/smile.png', cv2.IMREAD_UNCHANGED)
    smile_emoji = cv2.resize(smile_emoji, (50, 50))

    # 이모티콘 투명도 처리
    alpha_emoji = smile_emoji[:, :, 3] / 255.0
    color_emoji = smile_emoji[:, :, :3]

    # 이모티콘 이미지 읽기
    neutral_emoji = cv2.imread('/Users/soyoung/ml_project/emotion_proj/4/neutral.png', cv2.IMREAD_UNCHANGED)
    neutral_emoji = cv2.resize(neutral_emoji, (50, 50))

    # 이모티콘 투명도 처리
    alpha_emoji2 = neutral_emoji[:, :, 3] / 255.0
    color_emoji2 = neutral_emoji[:, :, :3]
    return alpha_emoji,color_emoji,alpha_emoji2,color_emoji2

def model_load():
    # 모델 불러오기
    model = models.resnet18()
    model.fc = nn.Linear(in_features=512, out_features=7)
    model.conv1=nn.Conv2d(1, 64, kernel_size=(7, 7), stride=(2, 2), padding=(3, 3), bias=False)
    # pre trained model
    model.load_state_dict(torch.load("/Users/soyoung/ml_project/emotion_proj/4/best_model.pt"))
    model.to(device)
    return model

def model_pred(model,img,frame):

    pred = torch.stack([torch.tensor(im, dtype=torch.float32) for im in img])  # (N, 48, 48)
    pred = pred.permute(0, 3, 1, 2)
    pred_loader = DataLoader(pred, batch_size = BATCH_SIZE, shuffle=True) #drop_last = True

    for epoch in range(EPOCHS):
        with torch.no_grad():
            for img in pred_loader:
                pred = model(img.to(device))
                _, predicted = torch.max(pred.data, 1)  # 예측된 라벨

                h, w, _ = frame.shape
                roi = frame[h-50:h, w-50:w]
             # clear_output()
            if predicted == 3:
                emoji_alpha = alpha_emoji
                emoji_color = color_emoji
            else:
                emoji_alpha = alpha_emoji2
                emoji_color = color_emoji2

            # Perform emoji overlay on the ROI
            np.multiply(1.0 - emoji_alpha[:, :, np.newaxis], roi, out=roi, casting="unsafe")
            np.add(emoji_color * emoji_alpha[:, :, np.newaxis], roi, out=roi, casting="unsafe")


def webcam(model):
    #웹캠에서 영상을 읽어온다
    cap = cv2.VideoCapture(0)
    cap.set(3, 640) #WIDTH
    cap.set(4, 480) #HEIGHT
 
    #얼굴 인식 캐스케이드 파일 읽는다
    face_cascade = cv2.CascadeClassifier('/Users/soyoung/ml_project/emotion_proj/3/haarcascade_frontalface_alt.xml')
    count = 0
    model_input_size = (48, 48) # 모델에 입력되는 이미지 크기
    while(True):
    # frame 별로 capture 한다
        ret, frame = cap.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    #인식된 얼굴 갯수를 출력
        print(len(faces))

    # 인식된 얼굴에 사각형을 출력한다
        for (x,y,w,h) in faces:
             cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)

          # 추출된 얼굴 영역 이미지를 모델에 입력할 준비
             face_img = gray[y:y+h, x:x+w]
             face_img = cv2.resize(face_img, model_input_size)
             face_img = np.expand_dims(face_img, axis=0)
         # 모델에 입력되는 이미지는 일반적으로 채널 수가 3이기 때문에 채널 수를 1로 바꿔줌
             face_img = np.expand_dims(face_img, axis=-1) 

         # 모델에 입력하여 결과 출력
             model_pred(model,face_img,frame)
         

    #화면에 출력한다
        cv2.imshow('frame',frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        # Display the frame with emoji overlay

    cap.release()
    cv2.destroyAllWindows()

alpha_emoji, color_emoji, alpha_emoji2, color_emoji2 = load_emoji()
pre_model = model_load()
webcam(pre_model)