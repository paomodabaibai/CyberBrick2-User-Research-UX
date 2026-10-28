/* CyberBrick H5 demo data. All commerce and device activity is simulated. */
(function (global) {
  'use strict';

  var STORAGE_KEY = 'cyberbrick-h5-v1';
  var listeners = new Set();
  var persistenceStatus = { persistent: true, error: null };

  function copy(value) { return JSON.parse(JSON.stringify(value)); }
  function id(prefix) {
    return prefix + '-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 9);
  }
  function text(value, max) { return String(value == null ? '' : value).trim().slice(0, max); }
  function uniqueStrings(value) {
    return Array.isArray(value) ? Array.from(new Set(value.filter(function (item) { return typeof item === 'string'; }))) : [];
  }
  function storageFailed(error) {
    persistenceStatus = { persistent: false, error: String(error && (error.message || error.name) || '本地存储暂不可用') };
  }

  function initialState() {
    return {
      version: 1,
      posts: [
        { id: 'post-1', title: '第一台拳击机器人，终于动起来了！', body: '从接上第一块主控，到第一次挥拳，花了三个周末。舵机、连杆、外壳都是一点点调出来的，下一站：周末擂台见。', image: 'assets/robot.svg', author: '积木研究所', avatar: '积', color: '#e9e8e5', likes: 286, saves: 43, category: '造物', type: 'post', tags: ['拳击机器人', '我的第一件作品'], createdAt: '2026-10-22T09:30:00+08:00', imageRatio: 'portrait' },
        { id: 'post-2', title: '周末的快乐，是一场机器人擂台赛', body: '带上自己的机器人，认识同样爱折腾的人。友谊赛、改装分享，还有一整桌等你试用的模块。周六下午，线下见！', image: 'assets/activity.png', author: '小岛制造', avatar: '岛', color: '#171717', likes: 1200, saves: 27, category: '活动', type: 'post', tags: ['周末活动', '机器人擂台'], createdAt: '2026-10-22T08:00:00+08:00', imageRatio: 'landscape' },
        { id: 'post-3', title: '一块主控，无限种玩法', body: '同一块智能主控，可以是桌面小车的大脑，也可以连接摇杆变成控制器。把想法接起来，开始你的下一件作品。', image: 'assets/board.svg', author: '阿白', avatar: '白', color: '#dfe6ef', likes: 92, saves: 32, category: '模块', type: 'module', tags: ['智能主控', '模块分享'], createdAt: '2026-10-21T16:40:00+08:00', imageRatio: 'landscape' },
        { id: 'post-4', title: '从一张草图开始，做自己的控制器', body: '这次想做一个适合单手操作的控制器。把按键、摇杆和手握姿势都重新排了一遍，分享我的草图和搭建记录。', image: 'assets/diy.png', author: 'MOMO', avatar: 'M', color: '#e8e5e1', likes: 164, saves: 68, category: '灵感', type: 'post', tags: ['DIY', '控制器'], createdAt: '2026-10-21T12:00:00+08:00', imageRatio: 'portrait' },
        { id: 'post-5', title: '拳头虽小，出拳要有态度', body: '给机器人换上一对新的软质拳套。轻量结构加上柔软外层，运动时的姿态也更好看了，附件里是我的改装思路。', image: 'assets/fist.png', author: '一颗螺丝', avatar: '螺', color: '#f3e1df', likes: 172, saves: 41, category: '造物', type: 'accessory', tags: ['配件信息', '软质拳套'], createdAt: '2026-10-20T19:10:00+08:00', imageRatio: 'portrait' },
        { id: 'post-6', title: '让每一次转动，都更有力量', body: '高扭矩舵机的桌面测试记录：从空载运动到带连杆动作，试了几组不同速度。把慢动作拍下来，调参真的直观很多。', image: 'assets/motor.svg', author: '陈同学', avatar: '陈', color: '#e1e6e9', likes: 84, saves: 19, category: '模块', type: 'module', tags: ['高扭矩舵机', '测试记录'], createdAt: '2026-10-20T14:00:00+08:00', imageRatio: 'landscape' },
        { id: 'post-7', title: '我的桌面，住进了一位新朋友', body: '把闲置的小外壳和旧模块重新拼起来，做了一个会点头的小机器人。每天开工之前，它会先和我打个招呼。', image: 'assets/robot.svg', author: '小岛制造', avatar: '岛', color: '#e8e9de', likes: 307, saves: 59, category: '灵感', type: 'post', tags: ['桌面伙伴', '创意改装'], createdAt: '2026-10-19T18:20:00+08:00', imageRatio: 'portrait' },
        { id: 'post-8', title: '把你的想法，拼成下一种可能', body: '本周造物挑战：用不超过六个模块，做一件能帮上忙的小物。分享你的过程，和大家一起把它变得更好。', image: 'assets/activity.png', author: 'CyberBrick 官方', avatar: 'C', color: '#171717', likes: 423, saves: 92, category: '活动', type: 'post', tags: ['造物挑战', '一起动手'], createdAt: '2026-10-19T10:00:00+08:00', imageRatio: 'landscape' },
        { id: 'post-own-1', title: '我的第一台拳击机器人', body: '从最初的想法到亲手组装完成，终于拥有了自己的第一台拳击机器人。还在练习控制，但已经准备好迎接下一场友谊赛。', image: 'assets/robot.svg', author: '小白的造物间', authorId: 'self', avatar: '白', color: '#e9e8e5', likes: 286, saves: 38, category: '造物', type: 'post', tags: ['我的创作', '拳击机器人'], createdAt: '2026-10-18T16:00:00+08:00', imageRatio: 'portrait', isOwn: true },
        { id: 'post-own-2', title: '红色拳击手，装配完成', body: '红色拳套装上了！重新调整了手臂连接和出拳角度，分享一下今天完成的改装。每一个小变化，都是新一步。', image: 'assets/fist.png', author: '小白的造物间', authorId: 'self', avatar: '白', color: '#f3e1df', likes: 89, saves: 16, category: '造物', type: 'accessory', tags: ['我的创作', '配件改装'], createdAt: '2026-10-17T14:00:00+08:00', imageRatio: 'portrait', isOwn: true }
      ],
      products: [
        { id: 'servo', name: '高扭矩舵机', subtitle: '每一次转动，都更有力', price: 129, image: 'assets/motor.svg', category: '动力', type: '动力', description: '为灵活的机械动作提供稳定动力。适合机器人手臂、连杆机构与轻量机械结构。模块化接口，让你的下一次组装更简单。', compatibility: 'CyberBrick 2.0', badge: '人气模块', stock: 88, specs: { '类型': '数字舵机', '峰值扭矩': '20 kg·cm', '旋转范围': '180°', '连接方式': '模块接口', '兼容版本': 'CyberBrick 2.0' } },
        { id: 'controller', name: '智能主控模块', subtitle: '一块主控，无限可能', price: 199, image: 'assets/board-product.svg', category: '主控', type: '主控', description: '作品的思考中心。连接动力、感知与控制模块，把你的想法组织成可以运行的动作。适合从第一件作品开始使用。', compatibility: 'CyberBrick 2.0', badge: '创作核心', stock: 62, specs: { '连接方式': '蓝牙 / USB-C', '模块接口': '6 路', '供电方式': 'USB-C / 电池模块', '编程方式': '图形化编排', '兼容版本': 'CyberBrick 2.0' } },
        { id: 'sensor', name: '距离感知模块', subtitle: '让作品感知周围', price: 79, image: 'assets/board.svg', category: '感知', type: '感知', description: '让作品感知距离的变化。搭配智能主控，轻松尝试避障、接近触发和互动装置等玩法。', compatibility: 'CyberBrick 2.0', badge: '探索必备', stock: 106, specs: { '感知方式': '红外测距', '工作距离': '5–100 cm', '连接方式': '模块接口', '兼容版本': 'CyberBrick 2.0' } },
        { id: 'frame', name: '轻量结构套件', subtitle: '把脑海里的结构搭出来', price: 89, image: 'assets/diy.png', category: '结构', type: '结构', description: '一组适合反复拆装的连接件与结构板。留出改造空间，让每一次新的想法都有合适的支点。', compatibility: 'CyberBrick 2.0', badge: '自由搭建', stock: 75, specs: { '套件数量': '24 件', '材质': '工程塑料', '连接方式': '标准孔位 / 螺丝', '兼容版本': 'CyberBrick 2.0' } },
        { id: 'fist', name: '机器人拳套', subtitle: '为你的战队换个新造型', price: 59, image: 'assets/fist.png', category: '结构', type: '结构', description: '轻盈软质的外层，适配机器人手臂末端。用一点红蓝色彩，为你的作品加入鲜明个性。', compatibility: 'CyberBrick 2.0', badge: '红蓝限定', stock: 120, specs: { '套件数量': '左右各 1 件', '材质': '软质硅胶', '配色': '经典红 / 竞技蓝', '兼容版本': 'CyberBrick 2.0' } },
        { id: 'motor', name: '双轮驱动模块', subtitle: '让想象开始移动', price: 159, image: 'assets/motor.svg', category: '动力', type: '动力', description: '紧凑的双轮动力组合，适合搭建桌面小车和移动机器人。连接主控，试着为你的作品规划第一段路线。', compatibility: 'CyberBrick 2.0', badge: '进阶玩法', stock: 47, specs: { '驱动形式': '双电机差速', '轮径': '42 mm', '连接方式': '模块接口', '兼容版本': 'CyberBrick 2.0' } }
      ],
      cart: [],
      orders: [],
      drafts: [],
      profile: { name: '小白的造物间', bio: '让每一个想法，都有形状。', avatar: '白', handle: '028491', joinedAt: '2026-09-01', followers: 2400, creations: 12, location: '杭州' },
      likedIds: [],
      savedIds: [],
      following: ['CyberBrick 官方']
    };
  }

  function restore() {
    var base = initialState();
    var raw;
    try {
      raw = global.localStorage.getItem(STORAGE_KEY);
    } catch (error) {
      storageFailed(error);
      return base;
    }
    try {
      var saved = raw ? JSON.parse(raw) : null;
      if (!saved || saved.version !== 1) return base;
      if (Array.isArray(saved.posts) && saved.posts.length && saved.posts.every(function (p) { return p && typeof p.id === 'string' && typeof p.title === 'string'; })) base.posts = saved.posts;
      // Product information comes from this file, so updates cannot leave stale prices behind.
      if (Array.isArray(saved.cart)) base.cart = saved.cart.filter(function (item) {
        return item && base.products.some(function (p) { return p.id === item.productId; }) && Number.isFinite(item.quantity) && item.quantity > 0;
      }).map(function (item) { return { productId: item.productId, quantity: Math.min(99, Math.floor(item.quantity)) }; });
      ['orders', 'drafts'].forEach(function (key) { if (Array.isArray(saved[key])) base[key] = saved[key].filter(function (item) { return item && typeof item.id === 'string'; }); });
      if (saved.profile && typeof saved.profile === 'object') {
        base.profile = Object.assign(base.profile, saved.profile);
        base.profile.name = text(base.profile.name, 24) || '小白的造物间';
        base.profile.bio = text(base.profile.bio, 160);
      }
      ['likedIds', 'savedIds', 'following'].forEach(function (key) { base[key] = uniqueStrings(saved[key]); });
      ['likedIds', 'savedIds'].forEach(function (key) { base[key] = base[key].filter(function (postId) { return base.posts.some(function (post) { return post.id === postId; }); }); });
    } catch (_) { /* Corrupt saved data does not mean storage itself is unavailable. */ }
    return base;
  }

  var state = restore();

  function getState() { return copy(state); }
  function getPersistenceStatus() { return copy(persistenceStatus); }
  function commit() {
    try {
      global.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
      persistenceStatus = { persistent: true, error: null };
    } catch (error) {
      storageFailed(error); // Current session remains usable; the UI can explain the limitation.
    }
    listeners.forEach(function (listener) {
      try { listener(getState()); } catch (error) {
        if (global.console && global.console.error) global.console.error('CyberBrick subscriber error:', error);
      }
    });
  }
  function subscribe(listener) {
    if (typeof listener !== 'function') throw new TypeError('订阅者必须是函数');
    listeners.add(listener);
    return function () { listeners.delete(listener); };
  }
  function togglePost(postId, listKey, countKey) {
    var post = state.posts.find(function (entry) { return entry.id === postId; });
    if (!post) return false;
    var position = state[listKey].indexOf(postId);
    var active = position === -1;
    if (active) state[listKey].push(postId);
    else state[listKey].splice(position, 1);
    post[countKey] = Math.max(0, (Number(post[countKey]) || 0) + (active ? 1 : -1));
    commit();
    return active;
  }
  function updateCart(productId, delta) {
    if (!state.products.some(function (product) { return product.id === productId; })) return 0;
    delta = Number(delta);
    if (!Number.isFinite(delta) || delta === 0) return (state.cart.find(function (item) { return item.productId === productId; }) || {}).quantity || 0;
    delta = Math.trunc(delta);
    var item = state.cart.find(function (entry) { return entry.productId === productId; });
    var quantity = Math.max(0, Math.min(99, (item ? item.quantity : 0) + delta));
    if (!quantity) state.cart = state.cart.filter(function (entry) { return entry.productId !== productId; });
    else if (item) item.quantity = quantity;
    else state.cart.push({ productId: productId, quantity: quantity });
    commit();
    return quantity;
  }
  function checkout() {
    if (!state.cart.length) return null;
    var items = state.cart.map(function (item) {
      var product = state.products.find(function (entry) { return entry.id === item.productId; });
      return { productId: product.id, name: product.name, image: product.image, price: product.price, quantity: item.quantity };
    });
    var total = Math.round(items.reduce(function (sum, item) { return sum + item.price * item.quantity; }, 0) * 100) / 100;
    var order = { id: id('CB'), total: total, items: items, createdAt: new Date().toISOString(), status: '模拟订单', simulated: true };
    state.orders.unshift(order);
    state.cart = [];
    commit();
    return { id: order.id, total: order.total };
  }
  function publish(payload) {
    payload = payload || {};
    var title = text(payload.title, 120);
    if (!title) throw new Error('先为你的作品写一个标题');
    var kind = text(payload.type, 24) || 'post';
    var category = kind === 'module' || kind === '模块分享' ? '模块' : kind === 'accessory' || kind === '配件信息' ? '造物' : '灵感';
    var post = {
      id: id('post'), title: title, body: text(payload.body, 5000),
      image: text(payload.image, 10000000) || 'assets/diy.png',
      author: state.profile.name, authorId: 'self', avatar: state.profile.avatar,
      color: '#e8e5e1', likes: 0, saves: 0, category: category, type: kind,
      tags: category === '模块' ? ['模块分享'] : ['我的创作'],
      createdAt: new Date().toISOString(), imageRatio: 'portrait', isOwn: true
    };
    state.posts.unshift(post);
    if (payload.draftId) state.drafts = state.drafts.filter(function (draft) { return draft.id !== payload.draftId; });
    commit();
    return copy(post);
  }
  function saveDraft(payload) {
    payload = payload || {};
    var existing = payload.id ? state.drafts.find(function (draft) { return draft.id === payload.id; }) : null;
    var draft = {
      id: existing ? existing.id : id('draft'), type: text(payload.type, 24) || 'post',
      title: text(payload.title, 120), body: text(payload.body, 5000), image: text(payload.image, 10000000),
      createdAt: existing ? existing.createdAt : new Date().toISOString(), updatedAt: new Date().toISOString()
    };
    if (existing) state.drafts[state.drafts.indexOf(existing)] = draft;
    else state.drafts.unshift(draft);
    commit();
    return copy(draft);
  }
  function removeDraft(draftId) {
    var previous = state.drafts.length;
    state.drafts = state.drafts.filter(function (draft) { return draft.id !== draftId; });
    if (previous === state.drafts.length) return false;
    commit();
    return true;
  }
  function updateProfile(payload) {
    payload = payload || {};
    if (Object.prototype.hasOwnProperty.call(payload, 'name')) {
      var name = text(payload.name, 24);
      if (!name) throw new Error('昵称不能为空');
      state.profile.name = name;
      state.profile.avatar = Array.from(name)[0];
      state.posts.forEach(function (post) { if (post.isOwn || post.authorId === 'self') { post.author = name; post.avatar = state.profile.avatar; } });
    }
    if (Object.prototype.hasOwnProperty.call(payload, 'bio')) state.profile.bio = text(payload.bio, 160);
    commit();
    return copy(state.profile);
  }
  function toggleFollow(author) {
    author = text(author, 80);
    if (!author || author === state.profile.name) return false;
    var index = state.following.indexOf(author);
    if (index === -1) state.following.push(author);
    else state.following.splice(index, 1);
    commit();
    return index === -1;
  }
  function reset() {
    state = initialState();
    commit();
    return getState();
  }

  global.CBStore = Object.freeze({
    getState: getState, getPersistenceStatus: getPersistenceStatus, subscribe: subscribe,
    toggleLike: function (postId) { return togglePost(postId, 'likedIds', 'likes'); },
    toggleSave: function (postId) { return togglePost(postId, 'savedIds', 'saves'); },
    addToCart: function (productId) { return updateCart(productId, 1); },
    updateCart: updateCart, checkout: checkout, publish: publish,
    saveDraft: saveDraft, removeDraft: removeDraft, updateProfile: updateProfile,
    toggleFollow: toggleFollow, reset: reset
  });
})(window);
