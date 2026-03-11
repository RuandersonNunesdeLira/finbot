FROM node:20-alpine

WORKDIR /app

# Install deps
COPY package.json ./
RUN npm install

# Copy source
COPY . .

EXPOSE 5173

CMD ["npx", "vite", "--host"]
