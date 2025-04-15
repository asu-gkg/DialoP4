import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || '';

// 封装API调用
const api = {
  // 发送聊天消息
  sendMessage: async (message, conversationId = '') => {
    const response = await axios.post(`${API_URL}/api/chat`, {
      message,
      conversation_id: conversationId
    });
    return response.data;
  },

  // 上传论文
  uploadPaper: async (file, conversationId = '') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('conversation_id', conversationId);

    const response = await axios.post(`${API_URL}/api/upload-paper`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  },

  // 生成代码
  generateCode: async (paperId, codeType, conversationId = '') => {
    const response = await axios.post(`${API_URL}/api/generate-code`, {
      paper_id: paperId,
      code_type: codeType,
      conversation_id: conversationId
    });
    return response.data;
  },

  // 评估代码
  evaluateImplementation: async (paperId, codeId, conversationId = '') => {
    const response = await axios.post(`${API_URL}/api/evaluate-implementation`, {
      paper_id: paperId,
      code_id: codeId,
      conversation_id: conversationId
    });
    return response.data;
  },

  // 优化代码
  refineImplementation: async (paperId, codeId, feedback = '', conversationId = '') => {
    const response = await axios.post(`${API_URL}/api/refine-implementation`, {
      paper_id: paperId,
      code_id: codeId,
      feedback,
      conversation_id: conversationId
    });
    return response.data;
  }
};

export default api; 