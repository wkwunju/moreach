"use client";

import { useState, useEffect, useRef } from "react";
import createGlobe from "cobe";

interface Post {
  id: number;
  platform: "reddit" | "twitter" | "instagram" | "tiktok";
  username: string;
  content: string;
  hasImage?: boolean;
  hasVideo?: boolean;
  position?: { top?: string; bottom?: string; left?: string; right?: string };
}

const allPosts: Post[] = [
  // Reddit - 真实讨论话题
  { id: 1, platform: "reddit", username: "coffee_addict", content: "What's your go-to morning routine for staying focused?" },
  { id: 2, platform: "reddit", username: "bookworm_22", content: "Just finished 'Project Hail Mary' - any similar sci-fi recommendations?" },
  { id: 3, platform: "reddit", username: "homecook_pro", content: "Perfected my sourdough starter after 3 months. AMA!" },
  { id: 4, platform: "reddit", username: "budget_traveler", content: "Backpacked SE Asia for $20/day. Here's how I did it..." },
  { id: 5, platform: "reddit", username: "fitness_newbie", content: "Finally hit my first pull-up after 6 months of training!" },
  { id: 6, platform: "reddit", username: "plant_parent", content: "Why does my monstera have yellow leaves? Help!" },
  
  // Twitter/X - 短文风格
  { id: 7, platform: "twitter", username: "thoughtleader", content: "The future of work isn't remote or office. It's flexible, outcome-driven, and human-centered." },
  { id: 8, platform: "twitter", username: "creator_economy", content: "We're entering the 'passion economy' - 50M+ creators monetizing their expertise 📈" },
  { id: 9, platform: "twitter", username: "wellness_daily", content: "Reminder: Comparison is the thief of joy. Focus on your own journey ✨" },
  { id: 10, platform: "twitter", username: "tech_observer", content: "AI won't replace you. But someone using AI will." },
  { id: 11, platform: "twitter", username: "minimalist_life", content: "Deleted 3 apps today. Gained 2 hours. Worth it." },
  { id: 12, platform: "twitter", username: "morning_person", content: "5am club hits different when you actually go to bed on time 😅" },
  
  // Instagram - 图片导向
  { id: 13, platform: "instagram", username: "travel.wanderlust", content: "Golden hour in Santorini never gets old 🌅", hasImage: true },
  { id: 14, platform: "instagram", username: "foodie.shots", content: "Homemade ramen that took 8 hours to perfect 🍜", hasImage: true },
  { id: 15, platform: "instagram", username: "fitness.journey", content: "Transformation Tuesday: 1 year of consistent training 💪", hasImage: true },
  { id: 16, platform: "instagram", username: "minimal.home", content: "My cozy reading nook setup - link to furniture in bio 📚", hasImage: true },
  { id: 17, platform: "instagram", username: "street.photography", content: "The streets of Tokyo at 3am 🌃", hasImage: true },
  { id: 18, platform: "instagram", username: "plant.aesthetic", content: "My urban jungle is officially out of control 🌿", hasImage: true },
  
  // TikTok - 视频内容
  { id: 19, platform: "tiktok", username: "lifehacks.daily", content: "POV: You just learned the right way to fold a fitted sheet", hasVideo: true },
  { id: 20, platform: "tiktok", username: "cookinghacks", content: "Making restaurant-quality pasta in 15 minutes 🍝", hasVideo: true },
  { id: 21, platform: "tiktok", username: "productivity.tips", content: "My 5AM routine that changed my life (realistic version)", hasVideo: true },
  { id: 22, platform: "tiktok", username: "travel.tok", content: "Hidden gems in Bali that tourists don't know about", hasVideo: true },
  { id: 23, platform: "tiktok", username: "diy.creator", content: "Turning IKEA furniture into luxury pieces ✨", hasVideo: true },
  { id: 24, platform: "tiktok", username: "petcomedy", content: "My cat's reaction to the automatic feeder 😹", hasVideo: true },
];

export default function GlobeAnimation() {
  const [visiblePosts, setVisiblePosts] = useState<number[]>([]);
  const [displayedPosts, setDisplayedPosts] = useState<Post[]>([]);
  const activePostsRef = useRef<Post[]>([]); // 用 ref 跟踪当前活跃帖子
  const initializedRef = useRef(false); // 确保只初始化一次
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !(canvas instanceof HTMLCanvasElement)) return;

    let phi = 0;
    const size = 600;
    canvas.width = size * 2;
    canvas.height = size * 2;

    const gl =
      canvas.getContext("webgl2", { alpha: true }) ||
      canvas.getContext("webgl", { alpha: true });
    if (!gl) return;

    let globe: ReturnType<typeof createGlobe> | null = null;
    const start = () => {
      globe = createGlobe(canvas, {
        devicePixelRatio: 2,
        width: size * 2,
        height: size * 2,
        phi: 0,
        theta: 0,
        dark: 1,
        diffuse: 1.2,
        scale: 1,
        mapSamples: 5500,
        mapBrightness: 6.0,
        baseColor: [1, 1, 1],
        markerColor: [0.984, 0.984, 0.984],
        glowColor: [1, 1, 1],
        markers: [
          // 欧洲
          { location: [49.6116, 6.1319], size: 0.03 },    // 卢森堡
          { location: [51.5074, -0.1278], size: 0.03 },   // 伦敦
          { location: [48.8566, 2.3522], size: 0.03 },    // 巴黎
          { location: [52.5200, 13.4050], size: 0.03 },   // 柏林
          { location: [52.3676, 4.9041], size: 0.03 },    // 阿姆斯特丹
          // 亚洲
          { location: [39.9042, 116.4074], size: 0.03 },  // 北京
          { location: [31.2304, 121.4737], size: 0.03 },  // 上海
          { location: [22.5431, 114.0579], size: 0.03 },  // 深圳
          { location: [22.3193, 114.1694], size: 0.03 },  // 香港
          { location: [35.6762, 139.6503], size: 0.03 },  // 东京
          { location: [1.3521, 103.8198], size: 0.03 },   // 新加坡
          // 北美
          { location: [40.7128, -74.0060], size: 0.03 },  // 纽约
          { location: [37.7749, -122.4194], size: 0.03 }, // 旧金山
          { location: [34.0522, -118.2437], size: 0.03 }, // 洛杉矶
          { location: [43.6532, -79.3832], size: 0.03 },  // 多伦多
          // 其他
          { location: [-33.8688, 151.2093], size: 0.03 }, // 悉尼
          { location: [25.2048, 55.2708], size: 0.03 },   // 迪拜
        ],
        offset: [0, 0],
        onRender: (state) => {
          state.phi = phi;
          phi += 0.005;
        },
      });
    };

    const rafId = requestAnimationFrame(start);

    return () => {
      cancelAnimationFrame(rafId);
      globe?.destroy();
    };
  }, []);

  useEffect(() => {
    // 防止 React Strict Mode 导致的重复初始化
    if (initializedRef.current) {
      console.log('⚠️ useEffect 已经初始化过，跳过');
      return;
    }
    initializedRef.current = true;
    console.log('🎬 [START] 初始化帖子系统');
    
    // 定义所有位置及其可共存位置
    const allPositions = [
      // 左侧区域 (zone 0-6)
      { top: '5%', left: '-15%', zone: 0, compatibleZones: [7, 8, 9, 10, 11, 12, 13] },
      { top: '8%', left: '15%', zone: 1, compatibleZones: [7, 8, 9, 10, 11, 12, 13] },
      { top: '25%', left: '-22%', zone: 2, compatibleZones: [7, 8, 9, 10, 11, 12, 13] },
      { top: '45%', left: '-18%', zone: 3, compatibleZones: [7, 8, 9, 10, 11, 12, 13] },
      { top: '60%', left: '-20%', zone: 4, compatibleZones: [7, 8, 9, 10, 11, 12, 13] },
      { bottom: '8%', left: '-18%', zone: 5, compatibleZones: [7, 8, 9, 10, 11, 12, 13] },
      { bottom: '7%', left: '10%', zone: 6, compatibleZones: [7, 8, 9, 10, 11, 12, 13] },
      
      // 右侧区域 (zone 7-13)
      { top: '8%', right: '-18%', zone: 7, compatibleZones: [0, 1, 2, 3, 4, 5, 6] },
      { top: '7%', right: '8%', zone: 8, compatibleZones: [0, 1, 2, 3, 4, 5, 6] },
      { top: '28%', right: '-22%', zone: 9, compatibleZones: [0, 1, 2, 3, 4, 5, 6] },
      { top: '48%', right: '-18%', zone: 10, compatibleZones: [0, 1, 2, 3, 4, 5, 6] },
      { top: '65%', right: '-15%', zone: 11, compatibleZones: [0, 1, 2, 3, 4, 5, 6] },
      { bottom: '6%', right: '-20%', zone: 12, compatibleZones: [0, 1, 2, 3, 4, 5, 6] },
      { bottom: '5%', right: '-8%', zone: 13, compatibleZones: [0, 1, 2, 3, 4, 5, 6] },
    ];

    let postIndex = 0;
    const shuffledPosts = [...allPosts].sort(() => Math.random() - 0.5);
    let currentZone: number | null = null; // 记录当前帖子的位置

    // 添加新帖子
    const addPost = (mustUseCompatibleZones: boolean = false) => {
      let selectedPosition;
      
      if (mustUseCompatibleZones && currentZone !== null) {
        // 必须从当前帖子的可共存位置中选择
        const currentPos = allPositions.find(p => p.zone === currentZone);
        const compatiblePositions = allPositions.filter(p => 
          currentPos?.compatibleZones.includes(p.zone)
        );
        selectedPosition = compatiblePositions[Math.floor(Math.random() * compatiblePositions.length)];
      } else {
        // 随机选择任意位置
        selectedPosition = allPositions[Math.floor(Math.random() * allPositions.length)];
      }
      
      const newPost = {
        ...shuffledPosts[postIndex % shuffledPosts.length],
        position: { 
          top: selectedPosition.top, 
          bottom: selectedPosition.bottom, 
          left: selectedPosition.left, 
          right: selectedPosition.right 
        },
        zoneId: selectedPosition.zone
      };
      
      activePostsRef.current.push(newPost);
      setDisplayedPosts([...activePostsRef.current]);
      
      console.log(`✅ [${Date.now()}] 添加帖子 #${newPost.id} zone:${selectedPosition.zone} | 当前队列长度:${activePostsRef.current.length} | 队列:`, activePostsRef.current.map(p => `#${p.id}(zone:${(p as any).zoneId})`));
      
      // 更新当前zone
      currentZone = selectedPosition.zone;
      
      // 淡入效果
      setTimeout(() => {
        setVisiblePosts(prev => [...prev, newPost.id]);
      }, 100);
      
      postIndex++;
    };

    // 移除最早的帖子
    const removeOldest = () => {
      if (activePostsRef.current.length === 0) {
        console.log(`⚠️ [${Date.now()}] 尝试移除但队列为空`);
        return;
      }
      const oldestPost = activePostsRef.current.shift()!;
      setVisiblePosts(prev => prev.filter(id => id !== oldestPost.id));
      setDisplayedPosts([...activePostsRef.current]);
      
      console.log(`❌ [${Date.now()}] 移除帖子 #${oldestPost.id} zone:${(oldestPost as any).zoneId} | 当前队列长度:${activePostsRef.current.length} | 队列:`, activePostsRef.current.map(p => `#${p.id}(zone:${(p as any).zoneId})`));
      
      // 更新 currentZone 为剩余帖子的 zone
      if (activePostsRef.current.length > 0) {
        currentZone = (activePostsRef.current[0] as any).zoneId;
      }
    };

    // 时间线：明确的先退后进（调慢速度）
    addPost(false);              // 0ms: 帖子1进入
    setTimeout(() => addPost(true), 1000);  // 1000ms: 帖子2进入（屏幕：1, 2）
    
    // 后续：严格的退-进-退-进循环
    setTimeout(() => {
      removeOldest();            // 2500ms: 帖子1退出（屏幕：2）
      setTimeout(() => addPost(true), 150);  // 2650ms: 帖子3进入（屏幕：2, 3）
    }, 2500);
    
    setTimeout(() => {
      removeOldest();            // 4000ms: 帖子2退出（屏幕：3）
      setTimeout(() => addPost(true), 150);  // 4150ms: 帖子4进入（屏幕：3, 4）
    }, 4000);
    
    // 从5500ms开始，每1500ms一个周期（退出+进入）
    let cycleInterval: NodeJS.Timeout;
    setTimeout(() => {
      console.log('🔄 [LOOP START] 开始循环');
      // 第一次循环
      removeOldest();
      setTimeout(() => addPost(true), 150);
      
      // 后续每1500ms一次
      cycleInterval = setInterval(() => {
        removeOldest();
        setTimeout(() => addPost(true), 150);
      }, 1500);
    }, 5500);

    return () => {
      if (cycleInterval) {
        clearInterval(cycleInterval);
      }
      console.log('🛑 [CLEANUP] 清理定时器');
    };
  }, []);

  const getPlatformIcon = (platform: string) => {
    switch (platform) {
      case "reddit":
        return (
          <svg className="w-4 h-4 text-orange-500" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.111 3.111 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 12c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.561 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.687-.562-1.249-1.25-1.249z"/>
          </svg>
        );
      case "twitter":
        return (
          <svg className="w-4 h-4 text-gray-900" fill="currentColor" viewBox="0 0 24 24">
            <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
          </svg>
        );
      case "instagram":
        return (
          <svg className="w-4 h-4 text-pink-500" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2c2.717 0 3.056.01 4.122.06 1.065.05 1.79.217 2.428.465.66.254 1.216.598 1.772 1.153.509.5.902 1.105 1.153 1.772.247.637.415 1.363.465 2.428.047 1.066.06 1.405.06 4.122 0 2.717-.01 3.056-.06 4.122-.05 1.065-.218 1.79-.465 2.428a4.883 4.883 0 01-1.153 1.772c-.5.509-1.105.902-1.772 1.153-.637.247-1.363.415-2.428.465-1.066.047-1.405.06-4.122.06-2.717 0-3.056-.01-4.122-.06-1.065-.05-1.79-.218-2.428-.465a4.89 4.89 0 01-1.772-1.153 4.904 4.904 0 01-1.153-1.772c-.248-.637-.415-1.363-.465-2.428C2.013 15.056 2 14.717 2 12c0-2.717.01-3.056.06-4.122.05-1.066.217-1.79.465-2.428a4.88 4.88 0 011.153-1.772A4.897 4.897 0 015.45 2.525c.638-.248 1.362-.415 2.428-.465C8.944 2.013 9.283 2 12 2zm0 5a5 5 0 100 10 5 5 0 000-10zm6.5-.25a1.25 1.25 0 10-2.5 0 1.25 1.25 0 002.5 0zM12 9a3 3 0 110 6 3 3 0 010-6z"/>
          </svg>
        );
      case "tiktok":
        return (
          <svg className="w-4 h-4 text-gray-900" fill="currentColor" viewBox="0 0 24 24">
            <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"/>
          </svg>
        );
    }
  };

  return (
    <div className="relative w-full h-full min-h-[500px]">
      {/* Simple Globe Circle */}
      <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
        <div className="globe-circle" style={{ opacity: 0.91 }}>
          <canvas ref={canvasRef} className="globe-canvas" />
        </div>
      </div>

      {/* Floating Post Cards */}
      {displayedPosts.map((post) => (
        <div
          key={post.id}
          className={`absolute transition-all duration-700 ease-out transform ${
            visiblePosts.includes(post.id)
              ? "opacity-100 translate-y-0 translate-x-0 scale-100 rotate-0"
              : "opacity-0 translate-y-8 translate-x-4 scale-90 -rotate-3"
          }`}
          style={{
            top: post.position?.top,
            bottom: post.position?.bottom,
            right: post.position?.right,
            left: post.position?.left,
            transition: "all 0.7s cubic-bezier(0.34, 1.56, 0.64, 1)",
          }}
        >
          {/* Post Card - 缩小版本 */}
          <div className="bg-white rounded-xl p-3 shadow-xl border border-gray-200 w-56 hover:scale-105 transition-transform">
            <div className="flex items-center gap-2 mb-2">
              {getPlatformIcon(post.platform)}
              <span className="text-xs font-bold text-gray-900">@{post.username}</span>
            </div>
            
            <p className="text-xs text-gray-700 leading-relaxed mb-2">{post.content}</p>
            
            {/* 平台特性展示 */}
            {post.hasImage && (
              <div className="mb-2 rounded-lg overflow-hidden border border-gray-200 h-24 relative">
                {/* Mock 图片内容 - 渐变背景 + 图案 */}
                <div className="w-full h-full bg-gradient-to-br from-purple-200 via-pink-200 to-orange-200"></div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-12 h-12 bg-white/30 rounded-full backdrop-blur-sm flex items-center justify-center">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                </div>
              </div>
            )}
            
            {post.hasVideo && (
              <div className="mb-2 rounded-lg overflow-hidden border border-gray-200 h-24 relative">
                {/* Mock 视频内容 - 深色渐变背景 */}
                <div className="w-full h-full bg-gradient-to-br from-blue-300 via-cyan-200 to-teal-300"></div>
                {/* 播放按钮覆盖层 */}
                <div className="absolute inset-0 flex items-center justify-center bg-black/20">
                  <div className="w-14 h-14 bg-white/90 rounded-full flex items-center justify-center shadow-lg hover:scale-110 transition-transform cursor-pointer">
                    <svg className="w-6 h-6 text-gray-800 ml-1" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M8 5v14l11-7z" />
                    </svg>
                  </div>
                </div>
                {/* 视频时长标签 */}
                <div className="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-1.5 py-0.5 rounded">
                  0:{Math.floor(Math.random() * 60).toString().padStart(2, '0')}
                </div>
              </div>
            )}
            
            {/* Connection indicator - 更小 */}
            <div className="flex items-center gap-1.5 text-xs text-green-600 font-semibold">
              <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-xs">Match</span>
            </div>
          </div>
        </div>
      ))}

      <style jsx>{`
        .globe-circle {
          width: 600px;
          height: 600px;
          border-radius: 50%;
          overflow: hidden;
          position: relative;
          background: transparent;
        }

        .globe-canvas {
          width: 100%;
          height: 100%;
          display: block;
          border: none;
          outline: none;
        }

      `}</style>
    </div>
  );
}
