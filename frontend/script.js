// Configuração da URL da API Backend FastAPI
const API_BASE_URL = window.location.port === "80" || window.location.port === ""
  ? "/api"
  : "http://localhost:8000/api";

// Dicionário de Tradução das Classes do Modelo de Visão Computacional
const DEFEITOS_TRADUCAO = {
  "Scratch": "Risco / Arranhão",
  "Damage": "Dano na Superfície",
  "Hole": "Furo / Perfuração",
  "Corner": "Canto Irregular",
  "Crease": "Vinco / Dobra",
  "Damaged Corner": "Canto Danificado",
  "Edge Wear": "Desgaste de Borda",
  "Heavy Wear": "Desgaste Severo",
  "Tear": "Rasgo",
  "miscut": "Corte Desalinhado (Miscut)",
  "Miscut": "Corte Desalinhado (Miscut)",
  // Compatibilidade com termos em português anteriores
  "Corte Desalinhado (Miscut)": "Corte Desalinhado",
  "Risco na Superfície": "Risco na Superfície",
  "Mancha de Tinta": "Mancha de Tinta",
  "Impressão Borrada": "Impressão Borrada",
  "Bordas Irregulares": "Desgaste de Borda",
  "Cor Fora do Padrão": "Cor Fora do Padrão",
};

function traduzirDefeito(tipo) {
  if (!tipo) return "Defeito Indefinido";
  return DEFEITOS_TRADUCAO[tipo] || tipo;
}

// Estado Global da Aplicação
let chartInstance = null;
let currentLoteId = null;

// Inicialização da Aplicação ao Carregar a Página
document.addEventListener("DOMContentLoaded", () => {
  lucide.createIcons();
  initChart();
  fetchDashboardData();
  
  // Polling a cada 2 segundos para atualização em tempo real
  setInterval(fetchDashboardData, 2000);
});

// 1. Inicialização do Chart.js para Defeitos por Hora/Intervalo
function initChart() {
  const ctx = document.getElementById("chart-defetos").getContext("2d");
  
  chartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: [], // Intervalos de Horas (ex: "14:10", "14:15")
      datasets: [{
        label: "Cartas Defeituosas",
        data: [],
        backgroundColor: "rgba(244, 63, 94, 0.6)", // Rose Tailwind
        borderColor: "rgba(244, 63, 94, 1)",
        borderWidth: 1.5,
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: {
          grid: { color: "rgba(255, 255, 255, 0.05)" },
          ticks: { color: "#94a3b8", font: { size: 11 } }
        },
        y: {
          beginAtZero: true,
          grid: { color: "rgba(255, 255, 255, 0.05)" },
          ticks: { color: "#94a3b8", precision: 0, font: { size: 11 } }
        }
      }
    }
  });
}

// 2. Busca Todos os Dados da API (`/dashboard-summary`)
async function fetchDashboardData() {
  try {
    const response = await fetch(`${API_BASE_URL}/dashboard-summary`);
    if (!response.ok) throw new Error("Erro na comunicação com a API");
    
    const data = await response.json();
    
    updateLoteUI(data.lote);
    updateSistemaUI(data.sistema);
    updateDefectsFeedUI(data.ultimos_defeitos);
    updateChartUI(data.defeitos_por_horario);
    
    setConnectionStatus(true);
  } catch (error) {
    console.error("Falha ao buscar dados:", error);
    setConnectionStatus(false);
  }
}

// 3. Atualiza os Cards do Lote Ativo
function updateLoteUI(lote) {
  if (!lote || !lote.id) {
    document.getElementById("lote-id-display").innerText = "Sem Lote Ativo";
    document.getElementById("btn-toggle-lote").className = "flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition shadow-sm";
    document.getElementById("text-lote-btn").innerText = "Iniciar Lote";
    document.getElementById("icon-lote-btn").setAttribute("data-lucide", "play");
    lucide.createIcons();
    currentLoteId = null;
    return;
  }

  currentLoteId = lote.id;
  document.getElementById("lote-id-display").innerText = `#${lote.id}`;
  
  // Atualiza botão para Encerrar Lote
  document.getElementById("btn-toggle-lote").className = "flex items-center gap-2 bg-rose-600 hover:bg-rose-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition shadow-sm";
  document.getElementById("text-lote-btn").innerText = "Encerrar Lote";
  document.getElementById("icon-lote-btn").setAttribute("data-lucide", "square");
  lucide.createIcons();

  // Cálculo de Normais Implicito: Totais - Defeituosas
  const totais = lote.cartas_totais || 0;
  const defeituosas = lote.cartas_defeituosas || 0;
  const normais = Math.max(0, totais - defeituosas);
  
  // Cálculo de Taxas
  const yieldRate = totais > 0 ? ((normais / totais) * 100).toFixed(1) : 100;
  const defectRate = totais > 0 ? ((defeituosas / totais) * 100).toFixed(1) : 0;

  document.getElementById("lote-totais").innerText = totais.toLocaleString();
  document.getElementById("lote-normais").innerText = normais.toLocaleString();
  document.getElementById("lote-defeito").innerText = defeituosas.toLocaleString();
  
  document.getElementById("lote-yield").innerText = `${yieldRate}% OK`;
  document.getElementById("lote-defect-rate").innerText = `${defectRate}% Defeito`;
}

// 4. Atualiza as Métricas do Sistema
function updateSistemaUI(sistema) {
  if (!sistema) return;

  const totais = sistema.cartas_totais || 0;
  const defeituosas = sistema.cartas_defeituosas || 0;
  const normais = Math.max(0, totais - defeituosas);
  const yieldRate = totais > 0 ? ((normais / totais) * 100).toFixed(1) : 100;

  document.getElementById("sistema-totais").innerText = totais.toLocaleString();
  document.getElementById("sistema-normais").innerText = normais.toLocaleString();
  document.getElementById("sistema-defeituosas").innerText = defeituosas.toLocaleString();
  document.getElementById("sistema-yield").innerText = `${yieldRate}%`;
  
  // Sequência atual de defeitos
  const seq = sistema.sequencia_atual || 0;
  document.getElementById("sistema-sequencia").innerText = seq;

  // Alerta Visual de Sequência Alta (Trigger se >= 3 falhas seguidas)
  const alertBox = document.getElementById("alert-sequence");
  if (seq >= 3) {
    alertBox.classList.remove("hidden");
    document.getElementById("alert-seq-count").innerText = seq;
  } else {
    alertBox.classList.add("hidden");
  }
}

// 5. Renderiza o Feed de Fotos de Cartas Defeituosas
function updateDefectsFeedUI(defects) {
  const container = document.getElementById("defects-feed");
  container.innerHTML = "";

  if (!defects || defects.length === 0) {
    container.innerHTML = `
      <div class="col-span-full py-8 text-center text-slate-500 text-xs">
        Nenhum defeito registrado no lote ativo.
      </div>`;
    return;
  }

  defects.forEach(defect => {
    const timeFormatted = new Date(defect.timestamp).toLocaleTimeString("pt-BR", { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const confPercent = (defect.grau_confiabilidade * 100).toFixed(0);

    const nomeTraduzido = traduzirDefeito(defect.tipo_defeito);

    const cardHtml = `
      <div class="bg-slate-900 border border-slate-700/60 rounded-lg overflow-hidden group hover:border-slate-500 transition">
        <div class="relative h-28 bg-slate-950 flex items-center justify-center overflow-hidden">
          <img src="${defect.imagem}" alt="${nomeTraduzido}" class="object-cover w-full h-full group-hover:scale-105 transition duration-300" onerror="this.src='https://placehold.co/300x200/0f172a/94a3b8?text=Sem+Imagem'">
          <span class="absolute top-2 right-2 badge-confidence">${confPercent}% Conf.</span>
        </div>
        <div class="p-2.5">
          <div class="flex items-center justify-between mb-1">
            <span class="text-xs font-bold text-rose-400 truncate" title="${defect.tipo_defeito}">${nomeTraduzido}</span>
            <span class="text-[10px] text-slate-400 font-mono bg-slate-800 px-1 py-0.5 rounded border border-slate-700">${defect.tipo_defeito}</span>
          </div>
          <div class="flex items-center justify-between text-[11px] text-slate-400">
            <span>Lote #${defect.id_lote}</span>
            <span>${timeFormatted}</span>
          </div>
        </div>
      </div>
    `;
    container.innerHTML += cardHtml;
  });
}

// 6. Atualiza os Dados do Gráfico
function updateChartUI(dataPoints) {
  if (!chartInstance || !dataPoints) return;

  chartInstance.data.labels = dataPoints.map(p => p.horario);
  chartInstance.data.datasets[0].data = dataPoints.map(p => p.quantidade);
  chartInstance.update();
}

// 7. Alternar Estado do Lote (Iniciar / Encerrar)
async function toggleLote() {
  const endpoint = currentLoteId ? `${API_BASE_URL}/lote/encerrar` : `${API_BASE_URL}/lote/iniciar`;
  
  try {
    const response = await fetch(endpoint, { method: "POST" });
    if (response.ok) {
      fetchDashboardData();
    } else {
      alert("Erro ao alterar o estado do Lote.");
    }
  } catch (err) {
    console.error("Erro na requisição:", err);
  }
}

// 8. Indicador Visual de Conexão com o Servidor
function setConnectionStatus(isOnline) {
  const indicator = document.getElementById("status-indicator");
  const text = document.getElementById("status-text");

  if (isOnline) {
    indicator.className = "w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse";
    text.innerText = "Online";
    text.className = "text-xs text-slate-300 font-medium";
  } else {
    indicator.className = "w-2.5 h-2.5 rounded-full bg-rose-500";
    text.innerText = "Offline";
    text.className = "text-xs text-rose-400 font-medium";
  }
}