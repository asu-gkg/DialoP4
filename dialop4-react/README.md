# DialoP4 React 前端

这是DialoP4的React前端实现版本，原先使用HTML/JavaScript实现。

## 功能特性

- 上传和分析网络研究论文
- 生成P4、NS3或Python实现代码
- 评估和优化生成的代码
- 与AI助手进行对话

## 安装与运行

### 前端开发环境

在项目根目录运行以下命令启动React开发服务器：

```bash
# 安装依赖
npm install

# 启动开发服务器
npm start
```

开发服务器将在 http://localhost:3000 启动。

### 生产构建

```bash
# 构建生产版本
npm run build
```

构建后的文件将放在 `build` 目录中。

### 后端服务器

前端需要连接到Flask后端服务器。请确保先启动后端服务器：

```bash
# 在项目根目录运行
python run.py
```

后端服务器将在 http://localhost:5000 运行。

## 部署流程

1. 先构建React前端：
   ```bash
   cd dialop4-react
   npm run build
   ```

2. 启动Flask服务器，它将自动提供React构建文件：
   ```bash
   python run.py
   ```

3. 访问 http://localhost:5000 即可使用完整应用

## 技术栈

- React 18
- Bootstrap 5
- Axios (HTTP请求)
- Flask (后端)

## 目录结构

```
dialop4-react/
├── public/             # 静态资源
├── src/                # 源代码
│   ├── api/            # API服务
│   ├── components/     # React组件
│   ├── App.js          # 主应用组件
│   └── index.js        # 入口文件
├── package.json        # 项目依赖
└── README.md           # 项目文档
```

# Getting Started with Create React App

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

## Available Scripts

In the project directory, you can run:

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will reload when you make changes.\
You may also see any lint errors in the console.

### `npm test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

### `npm run eject`

**Note: this is a one-way operation. Once you `eject`, you can't go back!**

If you aren't satisfied with the build tool and configuration choices, you can `eject` at any time. This command will remove the single build dependency from your project.

Instead, it will copy all the configuration files and the transitive dependencies (webpack, Babel, ESLint, etc) right into your project so you have full control over them. All of the commands except `eject` will still work, but they will point to the copied scripts so you can tweak them. At this point you're on your own.

You don't have to ever use `eject`. The curated feature set is suitable for small and middle deployments, and you shouldn't feel obligated to use this feature. However we understand that this tool wouldn't be useful if you couldn't customize it when you are ready for it.

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).

### Code Splitting

This section has moved here: [https://facebook.github.io/create-react-app/docs/code-splitting](https://facebook.github.io/create-react-app/docs/code-splitting)

### Analyzing the Bundle Size

This section has moved here: [https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size](https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size)

### Making a Progressive Web App

This section has moved here: [https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app](https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app)

### Advanced Configuration

This section has moved here: [https://facebook.github.io/create-react-app/docs/advanced-configuration](https://facebook.github.io/create-react-app/docs/advanced-configuration)

### Deployment

This section has moved here: [https://facebook.github.io/create-react-app/docs/deployment](https://facebook.github.io/create-react-app/docs/deployment)

### `npm run build` fails to minify

This section has moved here: [https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify](https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify)
