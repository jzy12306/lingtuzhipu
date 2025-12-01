import React from 'react';

const NewHomePage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 flex items-center justify-center p-4">
      <div className="text-center">
        <h1 className="text-5xl font-bold text-white mb-6">
          欢迎来到灵图智谱
        </h1>
        <p className="text-xl text-slate-300 mb-12 max-w-3xl mx-auto">
          基于大语言模型的多智能体协作系统，实现从非结构化数据到知识图谱的自主构建、动态维护与智能推理
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <a 
            href="/login" 
            className="px-8 py-3 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white font-semibold transition-all duration-300 transform hover:scale-105"
          >
            登录
          </a>
          <a 
            href="/register" 
            className="px-8 py-3 rounded-lg border-2 border-cyan-500 hover:bg-cyan-500/10 text-white font-semibold transition-all duration-300 transform hover:scale-105"
          >
            注册
          </a>
        </div>
      </div>
    </div>
  );
};

export default NewHomePage;