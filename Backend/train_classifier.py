import os
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, models, transforms
from torch.utils.data import DataLoader
import argparse

def train_model(dataset_path, epochs=3):
    print(f"Loading dataset from {dataset_path}...")
    
    # 1. Data Augmentation and Transforms
    transform = transforms.Compose([
        transforms.Resize((224, 224)), # Standard ResNet size
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(10),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    # Load entire dataset
    dataset = datasets.ImageFolder(dataset_path, transform=transform)
    dataloader = DataLoader(dataset, batch_size=16, shuffle=True)
    class_names = dataset.classes
    print(f"Found class folders: {class_names}")

    from models.custom_cnn import BrainTumorCNN
    
    # 2. Setup Custom Brain Tumor CNN Classifier
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Training on device: {device}")
    
    model = BrainTumorCNN()
    model = model.to(device)
    
    criterion = nn.CrossEntropyLoss()
    # Boosted learning rate slightly for from-scratch training
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    # 3. Training Loop
    print("Starting Transfer Learning Training (This should be very fast)...")
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        corrects = 0
        
        for inputs, labels in dataloader:
            inputs = inputs.to(device)
            labels = labels.to(device)
            
            optimizer.zero_grad()
            
            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)
            loss = criterion(outputs, labels)
            
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item() * inputs.size(0)
            corrects += torch.sum(preds == labels.data)
            
        epoch_loss = running_loss / len(dataset)
        epoch_acc = corrects.double() / len(dataset)
        print(f"Epoch {epoch+1}/{epochs} - Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f}")
        
    # 4. Save Model 
    os.makedirs('models', exist_ok=True)
    save_path = 'models/custom_cnn_brain.pth'
    torch.save(model.state_dict(), save_path)
    
    print(f"\nSUCCESS! Custom BrainTumorCNN trained and saved to {save_path}")
    print(f"Class Mapping: {dataset.class_to_idx} (ensure 'no'=0, 'yes'=1)")
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Train ResNet Classifier")
    parser.add_argument('--folder', type=str, required=True, help="Path to dataset folder (with yes/no subfolders)")
    parser.add_argument('--epochs', type=int, default=4, help="Number of training epochs")
    args = parser.parse_args()
    
    train_model(args.folder, args.epochs)
