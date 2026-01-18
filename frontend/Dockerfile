# Step 1: Build the React app
FROM node:18 AS build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
# Set API base URL for Docker environment
ARG REACT_APP_API_BASE=http://localhost:8000
ENV REACT_APP_API_BASE=$REACT_APP_API_BASE
RUN npm run build

# Step 2: Serve the built app with nginx
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
