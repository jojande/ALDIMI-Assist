import os
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, models, transforms
from torch.utils.data import DataLoader

# 1. Configurar la GTX 1650 con CUDA
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"--- Ejecutando entrenamiento en: {device} ---")

# 2. Preprocesamiento y aumento de datos para las imágenes
data_transforms = {
    'train': transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomRotation(10), # Robustez ante fotos inclinadas por voluntarios
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
    'val': transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
}

# 3. Cargar las imágenes desde tu nueva estructura de carpetas
current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.abspath(os.path.join(current_dir, '..', 'datos', 'clasificador'))
image_datasets = {x: datasets.ImageFolder(os.path.join(data_dir, x), data_transforms[x]) for x in ['train', 'val']}
dataloaders = {x: DataLoader(image_datasets[x], batch_size=16, shuffle=True) for x in ['train', 'val']}
dataset_sizes = {x: len(image_datasets[x]) for x in ['train', 'val']}
class_names = image_datasets['train'].classes
print(f"Clases detectadas automáticamente: {class_names}")

# 4. Cargar MobileNetV3-Small (Transfer Learning)
model = models.mobilenet_v3_small(pretrained=True)

# Congelar las capas pre-entrenadas para entrenamiento rápido en tu GPU
for param in model.parameters():
    param.requires_grad = False

# Modificar la última capa lineal (classifier) para tus 4 clases específicas de ALDIMI
num_features = model.classifier[3].in_features
model.classifier[3] = nn.Linear(num_features, len(class_names))
model = model.to(device)

# 5. Definir la función de pérdida y el optimizador
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.classifier[3].parameters(), lr=0.001)

# 6. Bucle de entrenamiento básico (5 Épocas es suficiente para empezar)
num_epochs = 5
print("\n--- Iniciando Entrenamiento ---")
for epoch in range(num_epochs):
    for phase in ['train', 'val']:
        if phase == 'train':
            model.train()
        else:
            model.eval()

        running_loss = 0.0
        running_corrects = 0

        for inputs, labels in dataloaders[phase]:
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()

            with torch.set_grad_enabled(phase == 'train'):
                outputs = model(inputs)
                _, preds = torch.max(outputs, 1)
                loss = criterion(outputs, labels)

                if phase == 'train':
                    loss.backward()
                    optimizer.step()

            running_loss += loss.item() * inputs.size(0)
            running_corrects += torch.sum(preds == labels.data)

        epoch_loss = running_loss / dataset_sizes[phase]
        epoch_acc = running_corrects.double() / dataset_sizes[phase]
        print(f'Época {epoch+1}/{num_epochs} - [{phase.upper()}] Pérdida: {epoch_loss:.4f} Precisión (Acc): {epoch_acc:.4f}')

# 7. Guardar los pesos del modelo final entrenado
os.makedirs(os.path.join(current_dir, 'pesos'), exist_ok=True)
torch.save(model.state_dict(), os.path.join(current_dir, 'pesos', 'document_classifier.pth'))
print("\n¡Modelo entrenado con éxito! Pesos guardados en 'ia_models/pesos/document_classifier.pth'")