# 使用官方Node.js镜像作为构建阶段
FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/library/node:18-alpine AS build

# 设置工作目录
WORKDIR /app

# 复制package.json和package-lock.json
COPY package*.json ./

# 删除现有的node_modules，避免平台不兼容问题
RUN rm -rf node_modules package-lock.json && \
    npm install

# 复制项目代码
COPY . .

# 构建应用（使用多页面配置）
RUN npm run build:multipage

# 使用Nginx作为生产环境服务器
FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/nginx:alpine

# 复制构建产物到Nginx静态目录
COPY --from=build /app/dist /usr/share/nginx/html

# 复制main.js文件（传统JavaScript文件，非模块化构建）
COPY --from=build /app/main.js /usr/share/nginx/html/main.js

# 复制自定义Nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露80端口
EXPOSE 80

# 启动Nginx
CMD ["nginx", "-g", "daemon off;"]