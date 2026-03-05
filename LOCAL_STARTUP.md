# TraderX Local Startup Guide

## Prerequisites

### Java 21 (via SDKMAN)

**macOS:**
```bash
sdk install java 21.0.10-tem
sdk use java 21.0.10-tem
```

**Linux:**
```bash
# Install SDKMAN if not already installed
curl -s "https://get.sdkman.io" | bash
source "$HOME/.sdkman/bin/sdkman-init.sh"

# Install and use Java 21
sdk install java 21.0.10-tem
sdk use java 21.0.10-tem
```

### Node.js 18 (via nvm)
```bash
nvm install 18
nvm use 18
```

### .NET 8

**macOS (via Homebrew):**
```bash
brew install dotnet@8
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y dotnet-sdk-8.0

# Fedora
sudo dnf install dotnet-sdk-8.0

# Or use the Microsoft install script
wget https://dot.net/v1/dotnet-install.sh -O dotnet-install.sh
chmod +x dotnet-install.sh
./dotnet-install.sh --channel 8.0
```

## Build Java Projects

From the project root:
```bash
./gradlew build
```

## Start Services

Start each service in its own terminal, in the following order.

### 1. Database (port 18082/18083/18084)
```bash
cd database
./run.sh
```

### 2. Reference Data (port 18085)
```bash
cd reference-data
npm install && npm run start
```

### 3. Trade Feed (port 18086)
```bash
cd trade-feed
npm install && npm run start
```

### 4. People Service (port 18089)

**macOS:**
```bash
cd people-service/PeopleService.WebApi
export DOTNET_ROOT="/opt/homebrew/opt/dotnet@8/libexec"
export PATH="/opt/homebrew/opt/dotnet@8/bin:$PATH"
dotnet run
```

**Linux:**
```bash
cd people-service/PeopleService.WebApi
dotnet run
```

### 5. Account Service (port 18088)
```bash
cd account-service
../gradlew bootRun
```

### 6. Position Service (port 18090)
```bash
cd position-service
../gradlew bootRun
```

### 7. Trade Processor (port 18091)
```bash
cd trade-processor
../gradlew bootRun
```

### 8. Trade Service (port 18092)
```bash
cd trade-service
../gradlew bootRun
```

### 9. Web Front-End — Angular (port 18093)
```bash
cd web-front-end/angular
npm install && npm run start
```

## Access the App

Open [http://localhost:18093](http://localhost:18093) in your browser.
