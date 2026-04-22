# ==========================================
# STAGE 1: Build the React Application
# ==========================================
# We use a Node.js image to install dependencies and build the app.
# The "build" process turns all the React code into plain HTML, CSS, and JS.
FROM node:18-alpine AS build_stage

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json first for caching
COPY package*.json ./

# Install all dependencies (including dev dependencies needed for the build)
RUN npm install

# Copy all the source code
COPY . .

# Run the build script (React creates a "build/" folder)
RUN npm run build

# ==========================================
# STAGE 2: Serve the App in Production
# ==========================================
# We use a tiny web server called "Nginx".
# This image is extremely small and very fast at serving static files.
FROM nginx:alpine

# Copy the "built" files from Stage 1 into the Nginx server folder
# We throw away the entire Node.js environment, source code, and node_modules!
COPY --from=build_stage /app/build /usr/share/nginx/html

# Optional: Adding custom Nginx config for React Router if needed
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80 (default HTTP port for Nginx)
EXPOSE 80

# Start Nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]
