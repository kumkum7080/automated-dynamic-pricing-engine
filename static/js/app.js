// Globals
let currentProduct = null;
let currentProductsList = [];
let simProductData = null;

// Document Ready
document.addEventListener("DOMContentLoaded", () => {
  checkSession();
  initPage();
  initBackgroundCanvas();
});

// Toast notification helper
function showToast(message, isError = false) {
  const toast = document.getElementById("toast-notify");
  const msgSpan = document.getElementById("toast-message");
  if (!toast || !msgSpan) return;
  
  msgSpan.textContent = message;
  toast.classList.remove("error");
  if (isError) {
    toast.classList.add("error");
  }
  
  toast.classList.add("active");
  setTimeout(() => {
    toast.classList.remove("active");
  }, 3000);
}

// Session management
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

function checkSession() {
  const token = getCookie("access_token") || sessionStorage.getItem("access_token");
  const username = sessionStorage.getItem("username");
  
  const authOnlyElements = document.querySelectorAll(".auth-only");
  const guestOnlyElements = document.querySelectorAll(".guest-only");
  const userGreetingSpan = document.getElementById("username-display");

  if (token && username) {
    authOnlyElements.forEach(el => el.style.display = "inline-flex");
    guestOnlyElements.forEach(el => el.style.display = "none");
    if (userGreetingSpan) {
      userGreetingSpan.textContent = username;
    }
  } else {
    authOnlyElements.forEach(el => el.style.display = "none");
    guestOnlyElements.forEach(el => el.style.display = "inline-flex");
    
    // Redirect if on auth-protected page
    const path = window.location.pathname;
    if (path === "/dashboard" || path === "/history") {
      window.location.href = "/";
    }
  }
}

function handleLogout() {
  fetch("/api/auth/logout", { method: "POST" })
    .then(() => {
      document.cookie = "access_token=; Max-Age=0; path=/;";
      sessionStorage.removeItem("access_token");
      sessionStorage.removeItem("username");
      sessionStorage.removeItem("role");
      showToast("Logged out successfully");
      setTimeout(() => {
        window.location.href = "/";
      }, 1000);
    });
}

// Page Router / Initializer
function initPage() {
  const path = window.location.pathname;
  
  if (path === "/" || path === "/index.html") {
    loadPublicProducts();
  } else if (path === "/dashboard" || path === "/dashboard.html") {
    loadDashboardData();
  } else if (path === "/history" || path === "/history.html") {
    loadHistoryData();
  }
}

// ----------------- AUTHENTICATION FORMS -----------------

function openAuthModal(mode) {
  const overlay = document.getElementById("auth-overlay");
  if (!overlay) return;
  
  overlay.classList.add("active");
  switchAuthMode(mode);
}

function closeAuthModal() {
  const overlay = document.getElementById("auth-overlay");
  if (overlay) overlay.classList.remove("active");
}

function switchAuthMode(mode) {
  const loginWrapper = document.getElementById("login-form-wrapper");
  const registerWrapper = document.getElementById("register-form-wrapper");
  
  if (mode === "login") {
    loginWrapper.style.display = "block";
    registerWrapper.style.display = "none";
  } else {
    loginWrapper.style.display = "none";
    registerWrapper.style.display = "block";
  }
}

function handleLoginSubmit(event) {
  event.preventDefault();
  const username = document.getElementById("login-username").value;
  const password = document.getElementById("login-password").value;
  
  fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password })
  })
  .then(res => {
    if (!res.ok) throw new Error("Invalid credentials");
    return res.json();
  })
  .then(data => {
    sessionStorage.setItem("access_token", data.access_token);
    sessionStorage.setItem("username", data.user.username);
    sessionStorage.setItem("role", data.user.role);
    closeAuthModal();
    showToast(`Welcome back, ${data.user.username}!`);
    setTimeout(() => {
      window.location.href = "/dashboard";
    }, 1000);
  })
  .catch(err => {
    showToast(err.message, true);
  });
}

function handleRegisterSubmit(event) {
  event.preventDefault();
  const username = document.getElementById("register-username").value;
  const password = document.getElementById("register-password").value;
  const role = document.getElementById("register-role").value;
  
  fetch("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password, role })
  })
  .then(res => {
    if (!res.ok) throw new Error("Registration failed");
    return res.json();
  })
  .then(() => {
    showToast("Registration successful! Logging in...");
    // Auto-login
    fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    })
    .then(res => res.json())
    .then(data => {
      sessionStorage.setItem("access_token", data.access_token);
      sessionStorage.setItem("username", data.user.username);
      sessionStorage.setItem("role", data.user.role);
      closeAuthModal();
      setTimeout(() => {
        window.location.href = "/dashboard";
      }, 1000);
    });
  })
  .catch(err => {
    showToast(err.message, true);
  });
}

// ----------------- LANDING PAGE SIMULATOR -----------------

function scrollToSimulator() {
  document.getElementById("simulator-title").scrollIntoView({ behavior: "smooth" });
}

// Fetch products list (with fallbacks if guest)
function loadPublicProducts() {
  // Try to load auth token if available, but landing page can also use mock data
  const token = sessionStorage.getItem("access_token");
  const headers = token ? { "Authorization": `Bearer ${token}` } : {};
  
  // Define default products for marketing simulator if server connection fails or unauthenticated
  const fallbackProducts = [
    { product_id: 101, product_name: "Titanium Smartwatch", base_cost: 120.0, current_price: 199.99, min_p: 125, max_p: 300 },
    { product_id: 102, product_name: "Wireless Headphones", base_cost: 80.0, current_price: 149.99, min_p: 85, max_p: 220 },
    { product_id: 103, product_name: "Premium Leather Messenger Bag", base_cost: 45.0, current_price: 89.99, min_p: 48, max_p: 160 },
    { product_id: 104, product_name: "Ergonomic Office Chair", base_cost: 110.0, current_price: 249.99, min_p: 115, max_p: 380 },
    { product_id: 105, product_name: "Mechanical Gaming Keyboard", base_cost: 35.0, current_price: 79.99, min_p: 38, max_p: 140 }
  ];

  fetch("/api/products", { headers })
    .then(res => {
      if (!res.ok) throw new Error("Authentication required for API products");
      return res.json();
    })
    .then(products => {
      currentProductsList = products;
      populateProductSelect(products);
    })
    .catch(() => {
      // Use marketing fallback products
      currentProductsList = fallbackProducts;
      populateProductSelect(fallbackProducts);
    });
}

function populateProductSelect(products) {
  const select = document.getElementById("sim-product-select");
  if (!select) return;
  select.innerHTML = "";
  
  products.forEach(p => {
    const opt = document.createElement("option");
    opt.value = p.product_id;
    opt.textContent = p.product_name;
    select.appendChild(opt);
  });
  
  loadSimulatorProduct();
}

function loadSimulatorProduct() {
  const select = document.getElementById("sim-product-select");
  if (!select) return;
  
  const product_id = parseInt(select.value);
  const prod = currentProductsList.find(p => p.product_id === product_id);
  if (!prod) return;
  
  currentProduct = prod;
  
  const slider = document.getElementById("price-slider");
  const minLabel = document.getElementById("price-min-label");
  const maxLabel = document.getElementById("price-max-label");
  
  // Set slider boundaries
  const minPrice = Math.round(prod.base_cost * 1.05);
  const maxPrice = Math.round(prod.current_price * 2.0);
  
  slider.min = minPrice;
  slider.max = maxPrice;
  slider.value = prod.current_price;
  
  minLabel.textContent = `$${minPrice.toFixed(2)}`;
  maxLabel.textContent = `$${maxPrice.toFixed(2)}`;
  
  runSimulation();
}

function runSimulation() {
  const slider = document.getElementById("price-slider");
  const valDisplay = document.getElementById("price-slider-value");
  if (!slider) return;
  
  const price = parseFloat(slider.value);
  valDisplay.textContent = `$${price.toFixed(2)}`;
  
  const token = sessionStorage.getItem("access_token");
  if (token) {
    // Authenticated request
    fetch(`/api/products/${currentProduct.product_id}/simulate?simulated_price=${price}`, {
      headers: { "Authorization": `Bearer ${token}` }
    })
    .then(res => res.json())
    .then(data => {
      updateSimUI(data.predicted_quantity, data.predicted_revenue, data.predicted_profit);
    });
  } else {
    // Pure mathematical mock simulation for unauthenticated marketing value
    const base = currentProduct.base_cost;
    const current = currentProduct.current_price;
    
    // Simulate linear demand curve Q = intercept - slope * P
    const diff = price - current;
    // Typical elasticity: 10 units at current price, decreasing by 0.08 per dollar increase
    const slope = 10 / (current - base);
    const predicted_qty = Math.max(0, Math.round(15 - slope * (price - base)));
    const revenue = predicted_qty * price;
    const profit = predicted_qty * (price - base);
    
    updateSimUI(predicted_qty, revenue, profit);
  }
}

function updateSimUI(qty, revenue, profit) {
  document.getElementById("sim-units").textContent = `${qty} units`;
  document.getElementById("sim-revenue").textContent = `$${revenue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
  document.getElementById("sim-profit").textContent = `$${profit.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
  
  // Update the simulation graph
  const slider = document.getElementById("price-slider");
  if (slider) {
    const selectedPrice = parseFloat(slider.value);
    updateSimulatorChart(selectedPrice, profit, revenue);
  }
}

// ----------------- DASHBOARD MANAGEMENT -----------------

function loadDashboardData() {
  const token = sessionStorage.getItem("access_token");
  if (!token) return;
  
  fetch("/api/products", {
    headers: { "Authorization": `Bearer ${token}` }
  })
  .then(res => res.json())
  .then(products => {
    currentProductsList = products;
    renderDashboardTable(products);
    renderDashboardStats(products);
    renderDashboardMasterChart(products);
  })
  .catch(err => {
    showToast("Error loading merchant data", true);
  });
}

function renderDashboardStats(products) {
  const total = products.length;
  const lowStock = products.filter(p => p.current_stock <= 5).length;
  const overstock = products.filter(p => p.current_stock >= 40).length;
  const optimizations = products.filter(p => p.current_price !== p.optimized_price).length;
  
  const t_el = document.getElementById("stat-total");
  const l_el = document.getElementById("stat-low-stock");
  const o_el = document.getElementById("stat-overstock");
  const op_el = document.getElementById("stat-optimizations");
  
  if (t_el) t_el.textContent = total;
  if (l_el) l_el.textContent = lowStock;
  if (o_el) o_el.textContent = overstock;
  if (op_el) op_el.textContent = optimizations;
}

function renderDashboardTable(products) {
  const tbody = document.getElementById("dashboard-table-body");
  if (!tbody) return;
  tbody.innerHTML = "";
  
  products.forEach(p => {
    const tr = document.createElement("tr");
    
    // Check Stock classes
    let stockClass = "";
    if (p.current_stock <= 5) stockClass = 'style="color:#f87171; font-weight:700;"';
    else if (p.current_stock >= 40) stockClass = 'style="color:#fbbf24;"';
    
    // Clean strategy badges
    let badgeClass = "badge-maintain";
    let strategyText = p.recommended_strategy;
    if (strategyText.includes("Surge")) badgeClass = "badge-scarcity";
    else if (strategyText.includes("Match")) badgeClass = "badge-competitor";
    else if (strategyText.includes("Liquidation")) badgeClass = "badge-liquidation";

    // Optimizations styling
    const optimizationAvailable = p.current_price !== p.optimized_price;
    const optStyle = optimizationAvailable ? 'style="color:var(--accent-secondary); font-weight:700;"' : '';
    
    tr.innerHTML = `
      <td style="font-weight:600;">${p.product_name}</td>
      <td ${stockClass}>${p.current_stock} units</td>
      <td>$${p.base_cost.toFixed(2)}</td>
      <td style="font-weight:600;">$${p.current_price.toFixed(2)}</td>
      <td ${optStyle}>$${p.optimized_price.toFixed(2)}</td>
      <td><span class="badge-strategy ${badgeClass}">${strategyText}</span></td>
      <td class="actions-cell">
        <button class="btn btn-outline" style="padding:0.4rem 0.8rem; font-size:0.8rem;" onclick="openSimModal(${p.product_id})">Simulate</button>
        ${optimizationAvailable ? `<button class="btn btn-primary" style="padding:0.4rem 0.8rem; font-size:0.8rem;" onclick="applyOptimizedPrice(${p.product_id})">Apply</button>` : ''}
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function applyOptimizedPrice(product_id) {
  const p = currentProductsList.find(x => x.product_id === product_id);
  if (!p) return;
  
  const token = sessionStorage.getItem("access_token");
  fetch(`/api/products/${product_id}/update-price`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
    body: JSON.stringify({
      new_price: p.optimized_price,
      strategy_applied: p.recommended_strategy
    })
  })
  .then(res => {
    if (!res.ok) throw new Error("Price update failed");
    return res.json();
  })
  .then(() => {
    showToast(`Price optimized to $${p.optimized_price.toFixed(2)} for ${p.product_name}!`);
    loadDashboardData();
  })
  .catch(err => {
    showToast(err.message, true);
  });
}

// ----------------- MODAL SIMULATOR -----------------

function openSimModal(product_id) {
  const overlay = document.getElementById("sim-modal-overlay");
  const prod = currentProductsList.find(x => x.product_id === product_id);
  if (!overlay || !prod) return;
  
  simProductData = prod;
  document.getElementById("sim-modal-title").textContent = `Optimize: ${prod.product_name}`;
  
  const slider = document.getElementById("modal-price-slider");
  const minLabel = document.getElementById("modal-min-label");
  const maxLabel = document.getElementById("modal-max-label");
  
  const minPrice = Math.round(prod.base_cost * 1.05);
  const maxPrice = Math.round(prod.current_price * 2.0);
  
  slider.min = minPrice;
  slider.max = maxPrice;
  slider.value = prod.current_price;
  
  minLabel.textContent = `$${minPrice.toFixed(2)}`;
  maxLabel.textContent = `$${maxPrice.toFixed(2)}`;
  
  overlay.classList.add("active");
  runModalSimulation();
}

function closeSimModal() {
  const overlay = document.getElementById("sim-modal-overlay");
  if (overlay) overlay.classList.remove("active");
}

function runModalSimulation() {
  const slider = document.getElementById("modal-price-slider");
  const valDisplay = document.getElementById("modal-slider-value");
  if (!slider) return;
  
  const price = parseFloat(slider.value);
  valDisplay.textContent = `$${price.toFixed(2)}`;
  
  const token = sessionStorage.getItem("access_token");
  fetch(`/api/products/${simProductData.product_id}/simulate?simulated_price=${price}`, {
    headers: { "Authorization": `Bearer ${token}` }
  })
  .then(res => res.json())
  .then(data => {
    document.getElementById("modal-units").textContent = `${data.predicted_quantity} units`;
    document.getElementById("modal-revenue").textContent = `$${data.predicted_revenue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    document.getElementById("modal-profit").textContent = `$${data.predicted_profit.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
  });
}

function applyModalPrice() {
  const slider = document.getElementById("modal-price-slider");
  if (!slider) return;
  const price = parseFloat(slider.value);
  const token = sessionStorage.getItem("access_token");
  
  fetch(`/api/products/${simProductData.product_id}/update-price`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
    body: JSON.stringify({
      new_price: price,
      strategy_applied: "🔧 Manual Slider Overlap Override"
    })
  })
  .then(res => {
    if (!res.ok) throw new Error("Price override failed");
    return res.json();
  })
  .then(() => {
    showToast(`Manual price set to $${price.toFixed(2)} for ${simProductData.product_name}`);
    closeSimModal();
    loadDashboardData();
  })
  .catch(err => {
    showToast(err.message, true);
  });
}

// ----------------- AUDIT HISTORY LOGS -----------------

function loadHistoryData() {
  const token = sessionStorage.getItem("access_token");
  if (!token) return;
  
  fetch("/api/logs", {
    headers: { "Authorization": `Bearer ${token}` }
  })
  .then(res => res.json())
  .then(logs => {
    renderHistoryTable(logs);
  })
  .catch(err => {
    showToast("Error loading audit records", true);
  });
}

function renderHistoryTable(logs) {
  const tbody = document.getElementById("history-table-body");
  if (!tbody) return;
  tbody.innerHTML = "";
  
  if (logs.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--color-text-muted);">No price overrides logged in the audit ledger yet.</td></tr>`;
    return;
  }
  
  logs.forEach(l => {
    const tr = document.createElement("tr");
    
    // Color adjustments indicating direction of price update
    const direction = l.new_price > l.original_price ? 
      '<span style="color:var(--accent-secondary);">▲</span>' : 
      '<span style="color:#f87171;">▼</span>';
      
    tr.innerHTML = `
      <td style="color:var(--color-text-muted); font-family:monospace;">#${l.log_id}</td>
      <td style="font-weight:600;">${l.product_name}</td>
      <td>$${l.original_price.toFixed(2)}</td>
      <td style="font-weight:600;">$${l.new_price.toFixed(2)} ${direction}</td>
      <td><span style="font-size:0.9rem;">${l.strategy_applied}</span></td>
      <td><span class="badge" style="margin:0; padding:0.25rem 0.5rem; text-transform:none; font-size:0.75rem;">${l.username || 'system'}</span></td>
      <td style="color:var(--color-text-muted); font-size:0.85rem;">${l.timestamp}</td>
    `;
    tbody.appendChild(tr);
  });
}

// ----------------- DATA VISUALIZATION INSIGHT CHARTS -----------------

function updateSimulatorChart(selectedPrice, selectedProfit, selectedRevenue) {
  const ctx = document.getElementById("simulator-chart");
  if (!ctx || !currentProduct) return;
  
  const slider = document.getElementById("price-slider");
  if (!slider) return;
  
  const minPrice = parseFloat(slider.min);
  const maxPrice = parseFloat(slider.max);
  const steps = 15;
  const stepSize = (maxPrice - minPrice) / (steps - 1 || 1);
  
  const pricePoints = [];
  const profitCurve = [];
  const revenueCurve = [];
  
  for (let i = 0; i < steps; i++) {
    const p = minPrice + i * stepSize;
    pricePoints.push(p);
    
    // Simulate linear demand locally for curve plotting
    const base = currentProduct.base_cost;
    const current = currentProduct.current_price;
    const slope = 10 / (current - base || 1);
    const qty = Math.max(0, Math.round(15 - slope * (p - base)));
    
    profitCurve.push(qty * (p - base));
    revenueCurve.push(qty * p);
  }
  
  const priceLabels = pricePoints.map(p => `$${p.toFixed(2)}`);
  
  if (window.simChartInstance) {
    window.simChartInstance.data.labels = priceLabels;
    window.simChartInstance.data.datasets[0].data = revenueCurve;
    window.simChartInstance.data.datasets[1].data = profitCurve;
    
    // Highlight active selected slider point
    window.simChartInstance.data.datasets[2].data = pricePoints.map(p => {
      if (Math.abs(p - selectedPrice) < stepSize / 1.8) return selectedProfit;
      return null;
    });
    window.simChartInstance.update('none'); // silent update (no layout jump)
  } else {
    window.simChartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels: priceLabels,
        datasets: [
          {
            label: 'Projected Gross Revenue ($)',
            data: revenueCurve,
            borderColor: 'rgba(13, 148, 136, 0.65)',
            backgroundColor: 'rgba(13, 148, 136, 0.05)',
            borderWidth: 2,
            fill: true,
            tension: 0.3,
            pointRadius: 0
          },
          {
            label: 'Projected Net Profit ($)',
            data: profitCurve,
            borderColor: '#059669',
            backgroundColor: 'rgba(5, 150, 105, 0.08)',
            borderWidth: 3,
            fill: true,
            tension: 0.3,
            pointRadius: 0
          },
          {
            label: 'Your Simulated Selection',
            data: pricePoints.map(p => {
              if (Math.abs(p - selectedPrice) < stepSize / 1.8) return selectedProfit;
              return null;
            }),
            borderColor: '#ea580c',
            backgroundColor: '#ea580c',
            pointRadius: 6,
            pointHoverRadius: 8,
            showLine: false
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
            labels: {
              font: { family: "'Plus Jakarta Sans', sans-serif", weight: '600', size: 12 },
              color: '#475569'
            }
          },
          tooltip: {
            mode: 'index',
            intersect: false
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { color: '#64748b', font: { family: 'monospace' } }
          },
          y: {
            grid: { color: 'rgba(15, 23, 42, 0.04)' },
            ticks: { color: '#64748b', font: { family: 'monospace' } }
          }
        }
      }
    });
  }
}

function renderDashboardMasterChart(products) {
  const ctx = document.getElementById("dashboard-master-chart");
  if (!ctx) return;
  
  const labels = products.map(p => p.product_name);
  const costData = products.map(p => p.base_cost);
  const activePriceData = products.map(p => p.current_price);
  const optPriceData = products.map(p => p.optimized_price);
  
  if (window.dashChartInstance) {
    window.dashChartInstance.data.labels = labels;
    window.dashChartInstance.data.datasets[0].data = costData;
    window.dashChartInstance.data.datasets[1].data = activePriceData;
    window.dashChartInstance.data.datasets[2].data = optPriceData;
    window.dashChartInstance.update();
  } else {
    window.dashChartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Wholesale Base Cost ($)',
            data: costData,
            backgroundColor: 'rgba(71, 85, 105, 0.15)',
            borderColor: 'rgba(71, 85, 105, 0.35)',
            borderWidth: 1.5,
            borderRadius: 4
          },
          {
            label: 'Active Selling Price ($)',
            data: activePriceData,
            backgroundColor: 'rgba(13, 148, 136, 0.75)',
            borderColor: '#0d9488',
            borderWidth: 1.5,
            borderRadius: 4
          },
          {
            label: 'Aura Optimized Price ($)',
            data: optPriceData,
            backgroundColor: 'rgba(5, 150, 105, 0.85)',
            borderColor: '#059669',
            borderWidth: 1.5,
            borderRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
            labels: {
              font: { family: "'Plus Jakarta Sans', sans-serif", weight: '600', size: 12 },
              color: '#475569'
            }
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { color: '#64748b', font: { family: "'Plus Jakarta Sans', sans-serif" } }
          },
          y: {
            grid: { color: 'rgba(15, 23, 42, 0.04)' },
            ticks: { color: '#64748b', font: { family: 'monospace' } }
          }
        }
      }
    });
  }
}

// Interactive Stock Market Doodles / Moving Grid Illusion Background Canvas
function initBackgroundCanvas() {
  const canvas = document.getElementById("bg-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  
  let width = canvas.width = window.innerWidth;
  let height = canvas.height = window.innerHeight;
  
  window.addEventListener("resize", () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  });
  
  // Color presets for green/slate corporate themes (No blue, no dark mode colors)
  const colorBases = [
    { r: 16, g: 185, b: 129, baseOpacity: 0.15 }, // Emerald Green
    { r: 13, g: 148, b: 136, baseOpacity: 0.15 }, // Teal Green
    { r: 71, g: 85, b: 105, baseOpacity: 0.12 }  // Corporate Slate Grey
  ];

  // Generate random stock chart lines
  const lines = [];
  const lineCount = 3;
  
  for (let i = 0; i < lineCount; i++) {
    const points = [];
    const pointCount = Math.ceil(width / 140) + 2;
    for (let j = 0; j < pointCount; j++) {
      points.push({
        x: j * 140,
        y: height * 0.35 + (i * height * 0.15) + (Math.random() - 0.5) * 100,
        targetY: height * 0.35 + (i * height * 0.15) + (Math.random() - 0.5) * 100,
        speed: 0.002 + Math.random() * 0.004
      });
    }
    const colorPreset = colorBases[i % colorBases.length];
    lines.push({
      points,
      r: colorPreset.r,
      g: colorPreset.g,
      b: colorPreset.b,
      opacity: colorPreset.baseOpacity,
      lineWidth: 1.5 + Math.random() * 1.5
    });
  }
  
  // Floating stock symbols/doodles
  const symbols = ["▲", "▼", "$", "QTY", "ELAST", "TREND", "PROFIT", "MARKET", "BULL", "BEAR", "%", "SECURE", "OPTIMAL"];
  const particles = [];
  for (let i = 0; i < 30; i++) {
    particles.push({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.3,
      vy: -0.2 - Math.random() * 0.3,
      text: symbols[Math.floor(Math.random() * symbols.length)],
      fontSize: 10 + Math.random() * 12,
      opacity: 0.14 + Math.random() * 0.16
    });
  }
  
  // Mock background data ticks
  const dataTicks = [];
  for (let i = 0; i < 6; i++) {
    dataTicks.push({
      x: Math.random() * width,
      y: Math.random() * height,
      val: (Math.random() * 200 + 40).toFixed(2),
      code: ["AAPL", "MSFT", "NVDA", "AURA", "TSLA", "AMZN"][i],
      change: (Math.random() * 5 * (Math.random() > 0.4 ? 1 : -1)).toFixed(1),
      opacity: 0.15 + Math.random() * 0.15
    });
  }
  
  function animate() {
    ctx.clearRect(0, 0, width, height);
    
    // Draw background grid lines (Stock Chart style grid)
    ctx.strokeStyle = "rgba(71, 85, 105, 0.05)";
    ctx.lineWidth = 1;
    const gridSize = 100;
    
    for (let x = 0; x < width; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    for (let y = 0; y < height; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }
    
    // Animate and draw trend curves
    lines.forEach(line => {
      ctx.beginPath();
      ctx.strokeStyle = `rgba(${line.r}, ${line.g}, ${line.b}, ${line.opacity})`;
      ctx.lineWidth = line.lineWidth;
      
      line.points.forEach((p, idx) => {
        // Smooth target updates
        p.y += (p.targetY - p.y) * p.speed;
        if (Math.abs(p.y - p.targetY) < 1) {
          p.targetY = height * 0.2 + (lines.indexOf(line) * height * 0.15) + (Math.random() - 0.5) * 140;
        }
        
        // Slow scrolling effect
        p.x -= 0.18;
        if (p.x < -140) {
          p.x = (line.points.length - 1) * 140;
          p.y = p.targetY = height * 0.2 + (lines.indexOf(line) * height * 0.15) + (Math.random() - 0.5) * 140;
        }
        
        if (idx === 0) {
          ctx.moveTo(p.x, p.y);
        } else {
          const prev = line.points[idx - 1];
          const xc = (p.x + prev.x) / 2;
          const yc = (p.y + prev.y) / 2;
          ctx.quadraticCurveTo(prev.x, prev.y, xc, yc);
        }
      });
      ctx.stroke();
      
      // Node indicator ticks
      line.points.forEach(p => {
        if (p.x > 0 && p.x < width) {
          ctx.fillStyle = `rgba(${line.r}, ${line.g}, ${line.b}, ${line.opacity * 2.2})`;
          ctx.beginPath();
          ctx.arc(p.x, p.y, 3, 0, Math.PI * 2);
          ctx.fill();
        }
      });
    });
    
    // Draw particles
    particles.forEach(p => {
      ctx.fillStyle = `rgba(71, 85, 105, ${p.opacity})`;
      ctx.font = `600 ${p.fontSize}px 'Outfit', sans-serif`;
      ctx.fillText(p.text, p.x, p.y);
      
      p.x += p.vx;
      p.y += p.vy;
      
      if (p.y < -30) {
        p.y = height + 30;
        p.x = Math.random() * width;
      }
      if (p.x < -30 || p.x > width + 30) {
        p.x = Math.random() * width;
        p.y = height + 30;
      }
    });
    
    // Draw mock data ticks (crawling stock ticker text)
    dataTicks.forEach(t => {
      const isPositive = parseFloat(t.change) >= 0;
      const color = isPositive ? "5, 150, 105" : "220, 38, 38"; // Professional dark green and red
      ctx.fillStyle = `rgba(${color}, ${t.opacity})`;
      ctx.font = "600 11px monospace";
      ctx.fillText(`${t.code} $${t.val} (${isPositive ? "+" : ""}${t.change}%)`, t.x, t.y);
      
      t.x -= 0.1;
      if (t.x < -150) {
        t.x = width + 50;
        t.y = Math.random() * height;
        t.val = (Math.random() * 200 + 40).toFixed(2);
        t.change = (Math.random() * 5 * (Math.random() > 0.4 ? 1 : -1)).toFixed(1);
      }
    });
    
    requestAnimationFrame(animate);
  }
  
  animate();
}
