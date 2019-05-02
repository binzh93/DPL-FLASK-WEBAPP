# from 
import torch
# import sys
from torchvision import transforms
from torch.autograd import Variable
import torch.nn.functional as F

from PIL import Image
# sys.path.append('../')
# print(sys.path)
from config.config import *

cfg = Animals

# print(cfg)

test_trainsform = transforms.Compose([
        transforms.Resize(cfg['SIZE']),
        transforms.ToTensor(),
        transforms.Normalize(cfg['MEANS'], cfg['STD'])
    ])



class AnimalPredict():

    def __init__(self):
        # self.size = input_size
        # self.model = torch.load()
        self.device = device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        if torch.cuda.is_available():
            
            self.model = torch.load(cfg['MODEL_FILE'])
        else:
            self.model = torch.load(cfg['MODEL_FILE'], map_location='cpu')
        
        self.transform = test_trainsform
        # get into inference state
        
        self.model.eval()
        print(cfg)

    def predict(self, file_path):
        img = Image.open(file_path)
        if img.mode != "RGB":
            img = img.convert("RGB")
        img = self.transform(img)

        img_tensor = img.unsqueeze_(0)

        input = Variable(img_tensor)
        
        if torch.cuda.is_available():
            # print("asdnjasdsakhj")
            input = input.to(self.device)
            output = self.model(input)
            index = output.data.cpu().numpy().argmax()
            prob = F.softmax(output).data.cpu().numpy()
        else:
            output = self.model(input)
            index = output.data.numpy().argmax()
            prob = F.softmax(output).data.numpy()
        #return index
        #print(topk_idx)
        print("-----------------------------")
        
        print(output)
        print(prob)
        print(type(index))
        print("=---------my model begin-------")
        print(index)
        print(prob)
        print("=---------my model end-------")
        return int(index), prob[0][index]
