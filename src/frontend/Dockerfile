# --- Stage 1: Build React app ---
FROM node:22.14.0-alpine AS build
WORKDIR /frontend_app

# Copy package.json and package-lock.json for installing dependencies
COPY package*.json  .
RUN npm install --frozen-lockfile

# Copy the rest of the application and build
COPY . .
RUN npm run build

# --- Stage 2: Development (Vite) ---
FROM node:22.14.0 AS development
WORKDIR /frontend_app

# Copy package.json and install dependencies
COPY package*.json .
RUN npm install --frozen-lockfile

# Copy the source code
COPY . .

# Expose port for Vite
EXPOSE 5173

# Run Vite development server
CMD ["npm", "run", "dev"]

# --- Stage 3: Production (Nginx) ---
FROM nginx:stable-alpine AS production

# Copy the built React app to Nginx's public folder
COPY --from=build /frontend_app/dist /usr/share/nginx/html

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]