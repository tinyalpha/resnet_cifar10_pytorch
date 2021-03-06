# coding: utf-8
from torchvision.datasets import CIFAR10
import torchvision.transforms as transforms
import torch.optim as optim
import torch.nn as nn
import torch
import csv
import sys

from network import ResNet6n


def test(model, testloader, criterion):
    # test model on testloader
    # return val_loss, val_acc
    
    model.eval()
    correct, total = 0, 0
    loss, counter = 0, 0
    
    with torch.no_grad():
        for (images, labels) in testloader:

            images = images.to(cuda)
            labels = labels.to(cuda)

            outputs = model(images)
            _, predicted = torch.max(outputs.data, 1)

            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            loss += criterion(outputs, labels).item()
            counter += 1
    
    return loss / counter, correct / total


if __name__ == "__main__":
    # choice a gpu
    cuda = torch.device('cuda')

    # load data
    transform_train = transforms.Compose([
        transforms.RandomCrop(32, padding = 4),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010))])
    transform_test = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010))])

    trainset = CIFAR10("~/dataset/cifar10", transform = transform_train, train = True)
    trainloader = torch.utils.data.DataLoader(trainset, batch_size = 128, shuffle = True, num_workers = 4)

    testset = CIFAR10("~/dataset/cifar10", transform = transform_test, train = False)
    testloader = torch.utils.data.DataLoader(testset, batch_size = 128, shuffle = False, num_workers = 4)

    # write header
    with open('log.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(["iteration", "train_loss", "val_loss", "acc", "val_acc"])

    # build model and optimizer
    model = ResNet6n(10, n = 5).to(cuda)
    criterion = nn.CrossEntropyLoss()
    # model.load_state_dict(torch.load("weights.pkl"))


    # train
    i = 0
    correct, total = 0, 0
    train_loss, counter = 0, 0

    for epoch in range(1000000):
        # iteration over all train data
        for data in trainloader:
            # update lr
            if i == 0:
                optimizer = optim.SGD(model.parameters(), lr = 1e-1, weight_decay = 1e-4, momentum = 0.9)
            elif i == 32000:
                optimizer = optim.SGD(model.parameters(), lr = 1e-2, weight_decay = 1e-4, momentum = 0.9)
            elif i == 48000:
                optimizer = optim.SGD(model.parameters(), lr = 1e-3, weight_decay = 1e-4, momentum = 0.9)
            elif i == 64000:
                print("training finished")
                sys.exit(0)

            # shift to train mode
            model.train()
            
            # get the inputs
            inputs, labels = data
            inputs = inputs.to(cuda)
            labels = labels.to(cuda)
            
            # forward + backward + optimize
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            # count acc,loss on trainset
            _, predicted = torch.max(outputs.data, 1)
            
            total += labels.size(0)
            correct += (predicted == labels).sum().item()        
            train_loss += loss.item()
            counter += 1

            if i % 100 == 0:
                # get acc,loss on trainset
                acc = correct / total
                train_loss /= counter
                
                # test
                val_loss, val_acc = test(model, testloader, criterion)

                print('iteration %d , epoch %d:  loss: %.4f  val_loss: %.4f  acc: %.4f  val_acc: %.4f' 
                      %(i, epoch, train_loss, val_loss, acc, val_acc))
                
                # save logs and weights
                with open('log.csv', 'a') as f:
                    writer = csv.writer(f)
                    writer.writerow([i, train_loss, val_loss, acc, val_acc])
                torch.save(model.state_dict(), 'weights.pkl')
                    
                # reset counters
                correct, total = 0, 0
                train_loss, counter = 0, 0

            i += 1

