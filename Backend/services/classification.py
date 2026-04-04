import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import os

from models.custom_cnn import BrainTumorCNN

MODEL_PATH = "models/custom_cnn_brain.pth"
_classifier = None
_transform = None

def get_classifier():
    global _classifier, _transform
    if _classifier is None:
        if not os.path.exists(MODEL_PATH):
            return None
            
        try:
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            model = BrainTumorCNN()
            
            model.load_state_dict(torch.load(MODEL_PATH, map_location=device, weights_only=True))
            model.eval()
            model.to(device)
            _classifier = model
            
            _transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
        except Exception as e:
            print(f"Failed to load ResNet Classifier: {e}")
            return None
            
    return _classifier, _transform

def predict_tumor(image_path: str):
    """
    Returns (tumor_detected_bool, confidence_float)
    """
    res = get_classifier()
    if res is None:
        return None, 0.0
        
    model, transform = res
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    try:
        img = Image.open(image_path).convert('RGB')
        input_tensor = transform(img).unsqueeze(0).to(device)
        
        with torch.no_grad():
            outputs = model(input_tensor)
            probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
            
            # ImageFolder alphabetically sorts: 'no' -> 0, 'yes' -> 1
            score_no = probabilities[0].item()
            score_yes = probabilities[1].item()
            
            tumor_detected = score_yes > score_no
            confidence = max(score_no, score_yes)
            
            return tumor_detected, float(confidence)
    except Exception as e:
        print(f"Classifier prediction error: {e}")
        return None, 0.0
