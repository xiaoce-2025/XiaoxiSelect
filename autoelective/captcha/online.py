"""
@Author : xiaoce2025
@File   : online.py
@Date   : 2025-08-29
"""

import base64
from io import BytesIO
import json
import requests
from PIL import Image, ImageOps
import torch
import torch.nn as nn
import numpy as np

from .captcha import Captcha
from ..config import BaseConfig
from .._internal import get_abs_path
from ..exceptions import OperationFailedError, OperationTimeoutError, RecognizerError
from ..logger import ConsoleLogger

logger = ConsoleLogger("captcha.online")


class ColorClassifier(nn.Module):
    def __init__(self, num_colors=3):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 8, kernel_size=5, stride=2, padding=2),
            nn.ReLU(),
            nn.BatchNorm2d(8),
            nn.Conv2d(8, 16, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.BatchNorm2d(16),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(16, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.BatchNorm2d(16),
            nn.AdaptiveAvgPool2d((4, 2))
        )
        self.classifier = nn.Sequential(
            nn.Linear(16 * 4 * 2, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, num_colors)
        )
    
    def forward(self, x):
        x = self.features(x)
        x = x.flatten(1)
        return self.classifier(x)


class LineClassifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 8, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(8, 16, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((4, 2))
        )
        self.classifier = nn.Sequential(
            nn.Linear(16 * 4 * 2, 16),
            nn.ReLU(),
            nn.Linear(16, 2)
        )
    
    def forward(self, x):
        x = self.features(x)
        x = x.flatten(1)
        return self.classifier(x)


class TwoStageClassifier:
    def __init__(self, color_model_path=None, line_model_path=None):
        self.color_model = ColorClassifier()
        self.line_model = LineClassifier()
        
        if color_model_path:
            self.color_model.load_state_dict(torch.load(color_model_path, map_location='cpu'))
        if line_model_path:
            self.line_model.load_state_dict(torch.load(line_model_path, map_location='cpu'))
        
        self.color_model.eval()
        self.line_model.eval()
        
    def _preprocess_image(self, image):
        """预处理图片，返回 [1, 3, H, W] 的 tensor"""
        image = image.resize((130, 52), Image.LANCZOS)
        img_array = np.array(image, dtype=np.float32) / 255.0
        img_array = img_array.transpose(2, 0, 1)
        
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape(3, 1, 1)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32).reshape(3, 1, 1)
        img_array = (img_array - mean) / std
        
        tensor = torch.from_numpy(img_array).float().unsqueeze(0)
        return tensor
        
    def predict(self, image):
        """image: PIL Image 对象"""
        image_tensor = self._preprocess_image(image)
        
        with torch.no_grad():
            color_logits = self.color_model(image_tensor)
            color_pred = torch.argmax(color_logits, dim=1).item()
            
            line_logits = self.line_model(image_tensor)
            line_pred = torch.argmax(line_logits, dim=1).item()
            
            category_map = {
                (0, 0): 0,
                (0, 1): 1,
                (1, 0): 2,
                (1, 1): 3,
                (2, 0): 4,
                (2, 1): 5,
            }
            
            return category_map[(color_pred, line_pred)]


class APIConfig(object):

    _DEFAULT_CONFIG_PATH = '../apikey.json'

    def __init__(self, path=_DEFAULT_CONFIG_PATH):
        # 存储配置文件路径
        self.path = get_abs_path(path)
        # 初始化加载配置
        self.reload()
        
    def reload(self):
        """重新加载配置文件"""
        try:
            with open(self.path, 'r') as handle:
                self._apikey = json.load(handle)
            # 验证配置完整性
            assert 'username' in self._apikey.keys(), "Missing 'username' in apikey"
            assert 'password' in self._apikey.keys(), "Missing 'password' in apikey"
            assert 'RecognitionTypeid' in self._apikey.keys(), "Missing 'RecognitionTypeid' in apikey"
        except FileNotFoundError:
            raise OperationFailedError(f"API config file not found at {self.path}")
        except json.JSONDecodeError:
            raise OperationFailedError(f"Invalid JSON format in {self.path}")
        except AssertionError as e:
            raise OperationFailedError(f"API config validation failed: {str(e)}")

    @property
    def uname(self):
        return self._apikey['username']

    @property
    def pwd(self):
        return self._apikey['password']

    @property
    def typeid(self):
        return int(self._apikey['RecognitionTypeid'])


class TTShituRecognizer(object):

    _RECOGNIZER_URL = "http://api.ttshitu.com/base64"
    _MODELS_DIR = 'models'
    _COLOR_MODEL = 'color_model.pth'
    _LINE_MODEL = 'line_model.pth'

    def __init__(self):
        self._config = APIConfig()
        
        color_model_path = get_abs_path(f'{self._MODELS_DIR}/{self._COLOR_MODEL}')
        line_model_path = get_abs_path(f'{self._MODELS_DIR}/{self._LINE_MODEL}')
        self._local_classifier = TwoStageClassifier(color_model_path, line_model_path)
        
    def recognize(self, raw):
        im = Image.open(BytesIO(raw))
        try:
            if im.is_animated:
                oim = im
                oim.seek(oim.n_frames-1)
                im = Image.new('RGB', oim.size)
                im.paste(oim)
        except AttributeError:
            pass
        
        category = self._local_classifier.predict(im)
        category_names = ['蓝色无干扰', '蓝色有干扰', '黑色无干扰', '黑色有干扰', '白色无干扰', '白色有干扰']
        logger.info(f"验证码类型判别结果: {category_names[category]} (类别编号: {category})")
        
        _typeid_ = self._config.typeid
        
        # 当类型为"白色有干扰"(类别5)时，对图片进行颜色反转处理
        if category == 5:
            logger.info("执行验证码抗干扰预处理")
            encode = TTShituRecognizer._to_b64_inverted(raw)
        else:
            if category == 1 or category == 3:
                logger.info("执行验证码抗干扰预处理")
            encode = TTShituRecognizer._to_b64(raw)
        data = {
            "username": self._config.uname, 
            "password": self._config.pwd,
            "image": encode,
            "typeid": _typeid_
        }
        try:
            result = json.loads(requests.post(TTShituRecognizer._RECOGNIZER_URL, json=data, timeout=20).text)
        except requests.Timeout:
            raise OperationTimeoutError(msg="Recognizer connection time out")
        except requests.ConnectionError:
            raise OperationFailedError(msg="Unable to coonnect to the recognizer")
        
        if result["success"]:
            return Captcha(result["data"]["result"], None, None, None, None)
        else:
            raise RecognizerError(msg="Recognizer ERROR: %s" % result["message"])

    def _to_b64(raw):
        im = Image.open(BytesIO(raw))
        try:
            if im.is_animated:
                oim = im
                oim.seek(oim.n_frames-1)
                im = Image.new('RGB', oim.size)
                im.paste(oim)
        except AttributeError:
            pass
        buffer = BytesIO()
        im.convert('RGB').save(buffer, format='JPEG')
        b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return b64

    def _to_b64_inverted(raw):
        """对图片进行颜色反转后转换为base64"""
        im = Image.open(BytesIO(raw))
        try:
            if im.is_animated:
                oim = im
                oim.seek(oim.n_frames-1)
                im = Image.new('RGB', oim.size)
                im.paste(oim)
        except AttributeError:
            pass
        # 颜色反转处理
        im = ImageOps.invert(im.convert('RGB'))
        buffer = BytesIO()
        im.save(buffer, format='JPEG')
        b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return b64