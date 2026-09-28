import React, { useState, useRef, useEffect } from 'react';
import { sendChatMessage, submitFeedback } from '../services/api';
import SourceBadge from '../components/SourceBadge';
import { Send, Bot, User, Sparkles, HelpCircle, CheckCircle2, FileText, CornerDownLeft, ThumbsUp, ThumbsDown } from 'lucide-react';

export default function Chatbot({ activeStudent }) {
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'bot',
      text: `Hello ${activeStudent?.name || 'Student'}! I am SafiBot, your college information assistant. I can help you with your examination timetable, syllabus explanations, eligible events, academic deadlines, and verified college information.`,
      query_type: 'general',
      sources: []
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [feedbackState, setFeedbackState] = useState({});
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const quickQuestions = [
    "How many UG programmes are available?",
    "How many PG programmes are available?",
    "What programmes does the college offer?",
    "What programmes are available in Computer Applications?",
    "What departments are there?",
    "Who is the HOD of Computer Applications?",
    "When is my next exam?",
    "Show my complete exam timetable.",
    "What events are relevant to me?",
    "Do I have any upcoming deadlines?",
    "Explain Unit 3 of Data Structures.",
    "What are the admission requirements?",
    "Explain the examination regulations.",
    "What facilities does the college provide?"
  ];

  const handleFeedback = async (msgId, userQuery, botAnswer, sourceTitle, feedbackType) => {
    setFeedbackState((prev) => ({ ...prev, [msgId]: feedbackType }));
    try {
      await submitFeedback({
        question: userQuery || 'College Question',
        answer: botAnswer,
        source: sourceTitle || 'SafiBot Verified Knowledge',
        feedback: feedbackType,
      });
    } catch (err) {
      console.error('Feedback submission error:', err);
    }
  };

  const handleSend = async (textToSend) => {
    const query = textToSend || input;
    if (!query.trim() || loading) return;

    const userMsg = {
      id: Date.now(),
      sender: 'user',
      text: query,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await sendChatMessage(
        activeStudent?.id,
        query,
        activeStudent?.course,
        activeStudent?.semester
      );

      const botMsg = {
        id: Date.now() + 1,
        sender: 'bot',
        user_query: query,
        text: res.answer,
        query_type: res.query_type,
        data: res.data,
        sources: res.sources || []
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: 'bot',
          text: `Error contacting SafiBot: ${err.message}`,
          query_type: 'error',
          sources: []
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const renderMessageContent = (text) => {
    // If the text contains markdown tables (e.g. for timetables)
    if (text.includes('|') && text.includes('---')) {
      const parts = text.split('\n\n');
      return (
        <div className="space-y-3">
          {parts.map((p, idx) => {
            if (p.includes('| Date') || p.includes('| Date / Day') || p.includes('| ---')) {
              const lines = p.trim().split('\n').filter(Boolean);
              if (lines.length > 2) {
                const headers = lines[0].split('|').map(s => s.trim()).filter(Boolean);
                const rows = lines.slice(2).map(l => l.split('|').map(s => s.trim()).filter(Boolean));
                return (
                  <div key={idx} className="overflow-x-auto my-2 rounded-lg border border-slate-200">
                    <table className="min-w-full text-xs text-left bg-white">
                      <thead className="bg-slate-100 text-slate-700 font-semibold uppercase text-[10px] tracking-wider">
                        <tr>
                          {headers.map((h, i) => (
                            <th key={i} className="px-3 py-2 border-b border-slate-200">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {rows.map((row, rIdx) => (
                          <tr key={rIdx} className={rIdx % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'}>
                            {row.map((cell, cIdx) => (
                              <td key={cIdx} className="px-3 py-2 text-slate-800 font-medium">{cell}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                );
              }
            }
            return <p key={idx} className="whitespace-pre-line leading-relaxed">{p}</p>;
          })}
        </div>
      );
    }

    return <p className="whitespace-pre-line leading-relaxed text-sm">{text}</p>;
  };

  const getQueryTypeBadge = (type) => {
    switch (type) {
      case 'exam_timetable':
        return <span className="text-[10px] bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full font-medium">Structured Timetable Query</span>;
      case 'class_timetable':
        return <span className="text-[10px] bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full font-medium">Class Routine Query</span>;
      case 'rag_syllabus':
        return <span className="text-[10px] bg-purple-100 text-purple-800 px-2 py-0.5 rounded-full font-medium">ChromaDB Syllabus RAG</span>;
      case 'events':
        return <span className="text-[10px] bg-teal-100 text-teal-800 px-2 py-0.5 rounded-full font-medium">Personalized Event Filter</span>;
      case 'deadlines_notices':
        return <span className="text-[10px] bg-red-100 text-red-800 px-2 py-0.5 rounded-full font-medium">Notice & Deadline Query</span>;
      case 'document_request':
        return <span className="text-[10px] bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full font-medium">Academic Document Retrieval</span>;
      default:
        return null;
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-140px)] min-h-[550px] bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
      
      {/* Chat Header */}
      <div className="bg-slate-50 px-5 py-3.5 border-b border-slate-200 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <img 
            src="/safibot-logo.svg" 
            alt="SafiBot Logo" 
            className="w-9 h-9 object-contain rounded-lg shrink-0" 
          />
          <div>
            <h3 className="font-bold text-slate-900 text-sm">SafiBot Assistant</h3>
            <p className="text-xs text-slate-500">
              Personalized for: <strong className="text-slate-700">{activeStudent?.course} (Sem {activeStudent?.semester})</strong>
            </p>
          </div>
        </div>

        <button
          onClick={() => setMessages([messages[0]])}
          className="text-xs text-slate-500 hover:text-slate-800 px-2.5 py-1 rounded-md border border-slate-200 hover:bg-slate-100 cursor-pointer"
        >
          Clear Chat
        </button>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4 bg-slate-50/30">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex items-start gap-3 ${
              msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'
            }`}
          >
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                msg.sender === 'user'
                  ? 'bg-slate-900 text-white'
                  : 'bg-emerald-50 border border-emerald-200 shadow-xs'
              }`}
            >
              {msg.sender === 'user' ? (
                <User className="w-4 h-4" />
              ) : (
                <img 
                  src="/safibot-logo.svg" 
                  alt="SafiBot" 
                  className="w-5 h-5 object-contain" 
                />
              )}
            </div>

            <div
              className={`max-w-[85%] sm:max-w-[75%] rounded-2xl p-4 text-xs sm:text-sm shadow-xs ${
                msg.sender === 'user'
                  ? 'bg-slate-900 text-white rounded-tr-none'
                  : 'bg-white border border-slate-200 text-slate-800 rounded-tl-none'
              }`}
            >
              {msg.sender === 'bot' && msg.query_type && (
                <div className="mb-2">
                  {getQueryTypeBadge(msg.query_type)}
                </div>
              )}

              {renderMessageContent(msg.text)}

              {/* Source citations */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-3 pt-3 border-t border-slate-100 space-y-1.5">
                  <div className="text-[11px] font-semibold text-slate-500 flex items-center gap-1">
                    <FileText className="w-3 h-3 text-emerald-600" />
                    <span>Verified Knowledge Sources:</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {msg.sources.map((src, idx) => (
                      <SourceBadge key={idx} source={src} />
                    ))}
                  </div>
                </div>
              )}

              {/* Continuous Knowledge Improvement: Interactive Feedback */}
              {msg.sender === 'bot' && msg.id !== 1 && (
                <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
                  <span className="font-medium">Was this answer helpful?</span>
                  {feedbackState[msg.id] ? (
                    <span className={`font-semibold flex items-center gap-1 ${feedbackState[msg.id] === 'helpful' ? 'text-emerald-600' : 'text-amber-600'}`}>
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      {feedbackState[msg.id] === 'helpful' ? 'Thank you! (Helpful 👍)' : 'Flagged for Admin Verification 👎'}
                    </span>
                  ) : (
                    <div className="flex items-center gap-1.5">
                      <button
                        type="button"
                        onClick={() => handleFeedback(msg.id, msg.user_query, msg.text, msg.sources?.[0]?.title || '', 'helpful')}
                        className="flex items-center gap-1 px-2.5 py-1 rounded-lg hover:bg-emerald-50 hover:text-emerald-700 text-slate-600 border border-slate-200 hover:border-emerald-300 transition-colors cursor-pointer"
                        title="Helpful"
                      >
                        <ThumbsUp className="w-3 h-3 text-emerald-600" />
                        <span>Helpful</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => handleFeedback(msg.id, msg.user_query, msg.text, msg.sources?.[0]?.title || '', 'not_helpful')}
                        className="flex items-center gap-1 px-2.5 py-1 rounded-lg hover:bg-rose-50 hover:text-rose-700 text-slate-600 border border-slate-200 hover:border-rose-300 transition-colors cursor-pointer"
                        title="Not Helpful"
                      >
                        <ThumbsDown className="w-3 h-3 text-rose-600" />
                        <span>Not Helpful</span>
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-emerald-600 text-white flex items-center justify-center">
              <Bot className="w-4 h-4" />
            </div>
            <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-none p-4 shadow-xs">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 rounded-full bg-emerald-600 animate-bounce"></div>
                <div className="w-2 h-2 rounded-full bg-emerald-600 animate-bounce [animation-delay:0.2s]"></div>
                <div className="w-2 h-2 rounded-full bg-emerald-600 animate-bounce [animation-delay:0.4s]"></div>
                <span className="text-xs text-slate-500 ml-1">Consulting knowledge base & RAG...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Questions Chips */}
      <div className="px-4 py-2.5 bg-white border-t border-slate-100 flex items-center gap-2 overflow-x-auto">
        <span className="text-[11px] font-semibold text-slate-600 shrink-0 flex items-center gap-1">
          <Sparkles className="w-3 h-3 text-amber-500" /> Suggestions:
        </span>
        {quickQuestions.map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(q)}
            className="text-xs text-slate-600 hover:text-emerald-700 bg-slate-100 hover:bg-emerald-50 border border-slate-200 hover:border-emerald-200 px-3 py-1 rounded-full whitespace-nowrap transition-colors cursor-pointer"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Chat Input */}
      <div className="p-3 sm:p-4 bg-white border-t border-slate-200">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={`Ask SafiBot a question about ${activeStudent?.course || 'college'}...`}
            className="flex-1 bg-slate-50 border border-slate-300 rounded-xl px-4 py-2.5 text-xs sm:text-sm text-slate-800 placeholder-slate-400 focus:outline-hidden focus:ring-2 focus:ring-emerald-500 focus:bg-white"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white px-4 py-2.5 rounded-xl font-medium flex items-center gap-1.5 transition-colors cursor-pointer shrink-0"
          >
            <Send className="w-4 h-4" />
            <span className="hidden sm:inline text-xs">Ask</span>
          </button>
        </form>
      </div>

    </div>
  );
}
