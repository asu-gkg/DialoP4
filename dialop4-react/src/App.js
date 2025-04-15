import React, { useState } from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap-icons/font/bootstrap-icons.css';
import './App.css';
import api from './api/api';

function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [messages, setMessages] = useState([
    {
      type: 'bot', 
      content: `您好！我是DialoP4，一个专门针对网络研究论文的智能助手。
      您可以：
      - 上传论文PDF进行分析
      - 生成P4、NS3或Python实现代码
      - 评估和优化生成的代码
      - 询问有关论文内容的问题
      
      请先上传一篇网络研究论文，或者询问我任何问题！`
    }
  ]);
  const [userInput, setUserInput] = useState('');
  const [paperAnalysis, setPaperAnalysis] = useState(null);
  const [codeType, setCodeType] = useState('python');
  const [generatedCode, setGeneratedCode] = useState(null);
  const [evaluation, setEvaluation] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleTabChange = (tab) => {
    setActiveTab(tab);
  };

  const handleUserInput = (e) => {
    setUserInput(e.target.value);
  };

  const sendMessage = async () => {
    if (!userInput.trim()) return;
    
    // 添加用户消息到聊天
    const newMessages = [...messages, { type: 'user', content: userInput }];
    setMessages(newMessages);
    setUserInput('');
    setIsLoading(true);

    try {
      // 调用API服务
      const data = await api.sendMessage(userInput);
      
      // 添加机器人回复
      setMessages([...newMessages, { type: 'bot', content: data.response }]);
    } catch (error) {
      console.error('聊天请求失败:', error);
      setMessages([...newMessages, { type: 'bot', content: '抱歉，发生了错误，请重试。' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      sendMessage();
    }
  };

  const uploadPaper = async (e) => {
    const file = e.target.files[0];
    if (!file || !file.name.endsWith('.pdf')) {
      alert('请上传PDF文件');
      return;
    }

    setIsLoading(true);

    try {
      // 调用API服务
      const data = await api.uploadPaper(file);
      
      if (data.analysis) {
        setPaperAnalysis(data.analysis);
        setMessages([
          ...messages, 
          { type: 'bot', content: `论文《${file.name}》上传成功！\n\n${data.analysis.summary}` }
        ]);
      } else {
        throw new Error(data.error || '上传失败');
      }
    } catch (error) {
      console.error('论文上传失败:', error);
      setMessages([...messages, { type: 'bot', content: `论文上传失败: ${error.message}` }]);
    } finally {
      setIsLoading(false);
      // 清空文件输入
      e.target.value = '';
    }
  };

  const generateCode = async () => {
    if (!paperAnalysis) {
      alert('请先上传并分析论文');
      return;
    }

    setIsLoading(true);

    try {
      // 调用API服务
      const data = await api.generateCode(paperAnalysis.id, codeType);
      
      setGeneratedCode(data.code);
      setActiveTab('code');
    } catch (error) {
      console.error('代码生成失败:', error);
      alert('代码生成失败，请重试');
    } finally {
      setIsLoading(false);
    }
  };

  const evaluateCode = async () => {
    if (!generatedCode) {
      alert('请先生成代码');
      return;
    }

    setIsLoading(true);

    try {
      // 调用API服务
      const data = await api.evaluateImplementation(paperAnalysis.id, generatedCode.id);
      
      setEvaluation(data.evaluation);
      setActiveTab('evaluation');
    } catch (error) {
      console.error('代码评估失败:', error);
      alert('代码评估失败，请重试');
    } finally {
      setIsLoading(false);
    }
  };

  const refineCode = async () => {
    if (!generatedCode || !evaluation) {
      alert('请先生成并评估代码');
      return;
    }

    setIsLoading(true);

    try {
      // 调用API服务
      const data = await api.refineImplementation(paperAnalysis.id, generatedCode.id);
      
      setGeneratedCode(data.refined_code);
      setActiveTab('code');
    } catch (error) {
      console.error('代码优化失败:', error);
      alert('代码优化失败，请重试');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <nav className="navbar navbar-expand-lg navbar-dark bg-primary">
        <div className="container-fluid">
          <a className="navbar-brand" href="#">
            <i className="bi bi-diagram-3"></i> DialoP4
          </a>
          <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
            <span className="navbar-toggler-icon"></span>
          </button>
          <div className="collapse navbar-collapse" id="navbarNav">
            <ul className="navbar-nav">
              <li className="nav-item">
                <a className="nav-link active" href="#">主页</a>
              </li>
              <li className="nav-item">
                <a className="nav-link" href="#" data-bs-toggle="modal" data-bs-target="#aboutModal">关于</a>
              </li>
            </ul>
          </div>
        </div>
      </nav>

      <div className="container-fluid mt-4">
        <div className="row">
          <div className="col-md-8">
            <ul className="nav nav-pills mb-3">
              <li className="nav-item">
                <button 
                  className={`nav-link ${activeTab === 'chat' ? 'active' : ''}`} 
                  onClick={() => handleTabChange('chat')}
                >
                  对话
                </button>
              </li>
              <li className="nav-item">
                <button 
                  className={`nav-link ${activeTab === 'code' ? 'active' : ''}`}
                  onClick={() => handleTabChange('code')}
                >
                  代码
                </button>
              </li>
              <li className="nav-item">
                <button 
                  className={`nav-link ${activeTab === 'evaluation' ? 'active' : ''}`}
                  onClick={() => handleTabChange('evaluation')}
                >
                  评估
                </button>
              </li>
            </ul>

            <div className="tab-content">
              {/* 对话标签页 */}
              <div className={`tab-pane fade ${activeTab === 'chat' ? 'show active' : ''}`}>
                <div className="chat-container">
                  <div className="messages-container">
                    {messages.map((message, index) => (
                      <div key={index} className={`message ${message.type === 'user' ? 'user-message' : 'bot-message'}`}>
                        <p style={{ whiteSpace: 'pre-line' }}>{message.content}</p>
                      </div>
                    ))}
                    {isLoading && (
                      <div className="message bot-message">
                        <div className="loading"></div> 处理中...
                      </div>
                    )}
                  </div>
                  <div className="message-input">
                    <div className="input-group">
                      <input 
                        type="text" 
                        className="form-control" 
                        placeholder="输入消息..." 
                        value={userInput}
                        onChange={handleUserInput}
                        onKeyPress={handleKeyPress}
                      />
                      <button className="btn btn-primary" onClick={sendMessage}>
                        <i className="bi bi-send"></i> 发送
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* 代码标签页 */}
              <div className={`tab-pane fade ${activeTab === 'code' ? 'show active' : ''}`}>
                <div className="code-container">
                  <div className="code-selection mb-3">
                    <label className="form-label">代码类型</label>
                    <div className="btn-group" role="group">
                      <input 
                        type="radio" 
                        className="btn-check" 
                        name="codeType" 
                        id="pythonCode" 
                        value="python" 
                        checked={codeType === 'python'}
                        onChange={() => setCodeType('python')}
                      />
                      <label className="btn btn-outline-primary" htmlFor="pythonCode">Python</label>
                      
                      <input 
                        type="radio" 
                        className="btn-check" 
                        name="codeType" 
                        id="ns3Code" 
                        value="ns3"
                        checked={codeType === 'ns3'}
                        onChange={() => setCodeType('ns3')}
                      />
                      <label className="btn btn-outline-primary" htmlFor="ns3Code">NS3</label>
                      
                      <input 
                        type="radio" 
                        className="btn-check" 
                        name="codeType" 
                        id="p4Code" 
                        value="p4"
                        checked={codeType === 'p4'}
                        onChange={() => setCodeType('p4')}
                      />
                      <label className="btn btn-outline-primary" htmlFor="p4Code">P4</label>
                    </div>
                    <button 
                      className="btn btn-primary ms-3"
                      onClick={generateCode}
                      disabled={isLoading}
                    >
                      <i className="bi bi-code-square"></i> 生成代码
                    </button>
                  </div>
                  <div id="codeOutput">
                    {generatedCode ? (
                      <pre>{generatedCode.content}</pre>
                    ) : (
                      <div className="alert alert-info">
                        请先上传并分析论文，然后选择代码类型生成实现代码。
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* 评估标签页 */}
              <div className={`tab-pane fade ${activeTab === 'evaluation' ? 'show active' : ''}`}>
                <div className="code-container">
                  <div className="mb-3">
                    <button 
                      className="btn btn-primary"
                      onClick={evaluateCode}
                      disabled={isLoading || !generatedCode}
                    >
                      <i className="bi bi-check-circle"></i> 评估代码
                    </button>
                    <button 
                      className="btn btn-outline-primary ms-2"
                      onClick={refineCode}
                      disabled={isLoading || !evaluation}
                    >
                      <i className="bi bi-lightning"></i> 优化代码
                    </button>
                  </div>
                  <div id="evaluationOutput">
                    {evaluation ? (
                      <div>
                        <h5>评估结果</h5>
                        <pre>{evaluation.content}</pre>
                      </div>
                    ) : (
                      <div className="alert alert-info">
                        请先生成代码，然后进行评估和优化。
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 右侧面板 */}
          <div className="col-md-4">
            <div className="action-panel">
              <h5 className="mb-3">上传论文</h5>
              <div className="mb-3">
                <input 
                  className="form-control" 
                  type="file" 
                  id="paperUpload" 
                  accept=".pdf"
                  onChange={uploadPaper}
                  disabled={isLoading}
                />
              </div>
              <div id="uploadStatus" className="mt-2">
                {isLoading && <div className="loading"></div>}
              </div>
              
              {paperAnalysis && (
                <div className="mt-4">
                  <h5 className="mb-3">论文分析</h5>
                  <div>
                    <h6>标题</h6>
                    <p>{paperAnalysis.title}</p>
                    <h6>摘要</h6>
                    <p>{paperAnalysis.abstract}</p>
                    <h6>关键点</h6>
                    <ul>
                      {paperAnalysis.key_points && paperAnalysis.key_points.map((point, index) => (
                        <li key={index}>{point}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 关于模态框 */}
      <div className="modal fade" id="aboutModal" tabIndex="-1">
        <div className="modal-dialog">
          <div className="modal-content">
            <div className="modal-header">
              <h5 className="modal-title">关于DialoP4</h5>
              <button type="button" className="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div className="modal-body">
              <p>DialoP4是一个基于大型语言模型的智能代理系统，专为网络研究设计。系统能够解析NSDI/SIGCOMM等顶级会议的网络论文，并自动生成对应的NS3模拟代码、P4代码、Python实现、评估报告和交互式可视化界面。</p>
              
              <h6>核心特性</h6>
              <ul>
                <li>多Agent协同：各个Agent负责不同职能，相互协作完成复杂任务</li>
                <li>迭代式思考：通过多轮自我优化避免浅层思考和"思维捷径"</li>
                <li>检索增强生成：融合网络领域专业知识库提升输出质量</li>
                <li>人机协作循环：支持人类专家反馈和指导</li>
              </ul>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
