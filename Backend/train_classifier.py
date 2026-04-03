import os
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, models, transforms
from torch.utils.data import DataLoader
import argparse
from collections import Counter

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

    # Calculate Class Weights to handle Imbalanced Dataset
    class_counts = dict(Counter(dataset.targets))
    total_samples = sum(class_counts.values())
    print(f"Class distribution: {class_counts}")
    
    weights = []
    for i in range(len(class_names)):
        # Inverse class frequency
        weight = total_samples / (len(class_names) * class_counts[i])
        weights.append(weight)
        
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    class_weights = torch.FloatTensor(weights).to(device)
    print(f"Calculated class weights: {class_weights}")

    # 2. Setup ResNet-18 Classifier (Transfer Learning for High Accuracy)
    print(f"Training on device: {device}")
    
    # Load pre-trained ResNet18
    model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    
    # Freeze the early layers so we don't destroy pre-trained features
    for param in model.parameters():
        param.requires_grad = False
        
    # Replace the final layer to predict 2 classes (Yes/No)
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, 2)
    model = model.to(device)
    
    # Use Weighted Loss to handle class imbalance
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    # Only train the final fully connected layer (much faster and no overfitting)
    optimizer = optim.Adam(model.fc.parameters(), lr=0.001)
    
    # 3. Training Loop
    print("Starting ResNet-18 Transfer Learning...")
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
    save_path = 'models/resnet18_brain.pth'
    torch.save(model.state_dict(), save_path)
    
    print(f"\nSUCCESS! ResNet-18 trained and saved to {save_path}")
    print(f"Class Mapping: {dataset.class_to_idx} (ensure 'no'=0, 'yes'=1)")
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Train ResNet-18 Classifier")
    parser.add_argument('--folder', type=str, required=True, help="Path to dataset folder (with yes/no subfolders)")
    parser.add_argument('--epochs', type=int, default=4, help="Number of training epochs")
    args = parser.parse_args()
    
    train_model(args.folder, args.epochs)
