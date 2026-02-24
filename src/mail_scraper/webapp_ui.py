from fastapi import FastAPI
from fastapi.responses import HTMLResponse

ui_app = FastAPI(title="Procurement Webapp UI", version="2.0.0")


@ui_app.get("/", response_class=HTMLResponse)
def home() -> str:
    return _HTML


_STAGES = [
    ("job_setup", "Job Setup"),
    ("budget_review", "Budget Review"),
    ("task_assignment", "Task Assignment"),
    ("material_check", "Material Check"),
    ("pricing_validation", "Pricing / PO"),
    ("vendor_coordination", "Vendor Coordination"),
    ("order_placement", "Order Placement"),
    ("order_confirmation", "Order Confirmation"),
    ("yard_pull", "Yard Pull"),
    ("material_receiving", "Material Receiving"),
    ("completion_check", "Completion Check"),
    ("completed", "Completed"),
]

_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Hurricane Fence - Procurement Platform</title>
<style>
:root{
  --bg:#0c111b;--sidebar:#101729;--surface:#151d30;--surface2:#1a2540;
  --border:#222e4a;--text:#e4eaf6;--muted:#8895b3;--accent:#3b82f6;
  --accent2:#6366f1;--green:#22c55e;--amber:#f59e0b;--red:#ef4444;
  --cyan:#06b6d4;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--text);display:flex;min-height:100vh}
button{cursor:pointer;font-family:inherit}
input,select{font-family:inherit}

/* Sidebar */
.sidebar{width:240px;background:var(--sidebar);border-right:1px solid var(--border);display:flex;flex-direction:column;flex-shrink:0;position:fixed;top:0;left:0;bottom:0;z-index:100}
.sidebar-brand{padding:20px 16px;border-bottom:1px solid var(--border)}
.sidebar-brand h1{font-size:15px;font-weight:700;color:var(--text);line-height:1.3}
.sidebar-brand p{font-size:11px;color:var(--muted);margin-top:4px}
.sidebar-nav{flex:1;padding:8px}
.nav-item{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:8px;font-size:13px;font-weight:500;color:var(--muted);cursor:pointer;transition:all .15s;border:none;background:none;width:100%;text-align:left}
.nav-item:hover{background:var(--surface);color:var(--text)}
.nav-item.active{background:var(--accent);color:#fff}
.nav-item .icon{width:18px;text-align:center;font-size:15px}
.nav-item .badge{margin-left:auto;background:var(--red);color:#fff;font-size:10px;padding:2px 7px;border-radius:99px;font-weight:700}
.sidebar-footer{padding:12px 16px;border-top:1px solid var(--border)}
.sidebar-footer select{width:100%;background:var(--surface);border:1px solid var(--border);color:var(--text);padding:8px;border-radius:6px;font-size:12px}
.sidebar-footer label{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;display:block;margin-bottom:4px}

/* Main */
.main{margin-left:240px;flex:1;display:flex;flex-direction:column;min-height:100vh}
.topbar{display:flex;align-items:center;justify-content:space-between;padding:16px 24px;border-bottom:1px solid var(--border);background:var(--sidebar)}
.topbar h2{font-size:18px;font-weight:600}
.topbar-actions{display:flex;gap:8px}
.btn{padding:8px 16px;border-radius:8px;font-size:12px;font-weight:600;border:1px solid var(--border);background:var(--surface);color:var(--text);transition:all .15s}
.btn:hover{background:var(--surface2)}
.btn-primary{background:var(--accent);border-color:var(--accent);color:#fff}
.btn-primary:hover{opacity:.9}
.btn-sm{padding:5px 10px;font-size:11px}
.btn-green{background:var(--green);border-color:var(--green);color:#fff}
.btn-amber{background:var(--amber);border-color:var(--amber);color:#000}
.btn-red{background:var(--red);border-color:var(--red);color:#fff}
.content{flex:1;padding:24px;overflow-y:auto}

/* Dashboard KPI */
.kpi-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-bottom:20px}
.kpi{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px}
.kpi-label{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;margin-bottom:6px}
.kpi-value{font-size:26px;font-weight:700}
.kpi-sub{font-size:11px;color:var(--muted);margin-top:4px}

/* Board */
.board{display:flex;gap:10px;overflow-x:auto;padding-bottom:12px;align-items:flex-start}
.lane{min-width:240px;max-width:260px;flex-shrink:0;background:var(--surface);border:1px solid var(--border);border-radius:10px;display:flex;flex-direction:column;max-height:calc(100vh - 180px)}
.lane-header{padding:10px 12px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;background:var(--surface);border-radius:10px 10px 0 0;z-index:1}
.lane-title{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}
.lane-count{font-size:11px;background:var(--surface2);padding:2px 8px;border-radius:99px;color:var(--text);font-weight:600}
.lane-body{padding:6px;overflow-y:auto;flex:1;display:flex;flex-direction:column;gap:6px}
.card{background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:10px;cursor:pointer;transition:border-color .15s}
.card:hover{border-color:var(--accent)}
.card-job{font-size:13px;font-weight:700;color:var(--accent);margin-bottom:4px}
.card-vendor{font-size:11px;color:var(--muted);margin-bottom:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.card-row{display:flex;justify-content:space-between;align-items:center;font-size:11px}
.card-amount{font-weight:600}
.pill{display:inline-block;font-size:10px;padding:2px 8px;border-radius:99px;font-weight:600}
.pill-high{background:rgba(239,68,68,.15);color:var(--red)}
.pill-normal{background:rgba(59,130,246,.12);color:var(--accent)}
.pill-human{background:rgba(245,158,11,.15);color:var(--amber)}
.pill-auto{background:rgba(34,197,94,.12);color:var(--green)}

/* Table */
.data-table{width:100%;border-collapse:collapse;font-size:12px}
.data-table th{text-align:left;padding:10px 12px;background:var(--surface2);color:var(--muted);font-weight:600;text-transform:uppercase;font-size:10px;letter-spacing:.04em;border-bottom:1px solid var(--border);position:sticky;top:0;z-index:1}
.data-table td{padding:10px 12px;border-bottom:1px solid var(--border);vertical-align:middle}
.data-table tr:hover td{background:rgba(59,130,246,.04)}
.table-wrap{background:var(--surface);border:1px solid var(--border);border-radius:10px;overflow:auto;max-height:calc(100vh - 260px)}

/* Detail panel */
.detail-overlay{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.5);z-index:200;display:none;align-items:flex-start;justify-content:flex-end}
.detail-overlay.open{display:flex}
.detail-panel{width:460px;max-width:90vw;background:var(--sidebar);border-left:1px solid var(--border);height:100vh;overflow-y:auto;padding:24px;animation:slideIn .2s ease}
@keyframes slideIn{from{transform:translateX(100%)}to{transform:translateX(0)}}
.detail-panel h3{font-size:16px;margin-bottom:16px}
.detail-field{margin-bottom:12px}
.detail-field label{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;display:block;margin-bottom:4px}
.detail-field .val{font-size:14px}
.detail-actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:20px;padding-top:16px;border-top:1px solid var(--border)}

/* Activity */
.activity-item{display:flex;gap:12px;padding:12px 0;border-bottom:1px solid var(--border)}
.activity-dot{width:8px;height:8px;border-radius:50%;margin-top:5px;flex-shrink:0}
.activity-dot.auto{background:var(--green)}
.activity-dot.human{background:var(--amber)}
.activity-text{font-size:13px;flex:1}
.activity-meta{font-size:11px;color:var(--muted);margin-top:2px}

/* Responsive */
@media(max-width:900px){
  .sidebar{width:60px}
  .sidebar-brand p,.nav-item span:not(.icon),.sidebar-footer label{display:none}
  .sidebar-brand h1{font-size:11px;text-align:center}
  .main{margin-left:60px}
  .nav-item{justify-content:center;padding:12px}
}

.page{display:none}
.page.active{display:block}
.status-dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px}
.status-dot.green{background:var(--green)}
.status-dot.amber{background:var(--amber)}
.status-dot.red{background:var(--red)}
.status-dot.blue{background:var(--accent)}
.empty-state{text-align:center;padding:40px 20px;color:var(--muted);font-size:13px}
</style>
</head>
<body>

<aside class="sidebar">
  <div class="sidebar-brand">
    <h1>Hurricane Fence</h1>
    <p>Procurement Platform</p>
  </div>
  <nav class="sidebar-nav">
    <button class="nav-item active" data-page="dashboard">
      <span class="icon">&#9632;</span><span>Dashboard</span>
    </button>
    <button class="nav-item" data-page="board">
      <span class="icon">&#9776;</span><span>Job Board</span>
    </button>
    <button class="nav-item" data-page="approvals">
      <span class="icon">&#10003;</span><span>Approvals</span>
      <span class="badge" id="approvalBadge" style="display:none">0</span>
    </button>
    <button class="nav-item" data-page="vendors">
      <span class="icon">&#9733;</span><span>Vendors</span>
    </button>
    <button class="nav-item" data-page="activity">
      <span class="icon">&#8635;</span><span>Activity</span>
    </button>
  </nav>
  <div class="sidebar-footer">
    <label>Acting As</label>
    <select id="userEmail">
      <option value="buyer@hurricanefence.com">Buyer</option>
      <option value="approver@hurricanefence.com">Approver</option>
      <option value="admin@hurricanefence.com">Admin</option>
    </select>
  </div>
</aside>

<div class="main">
  <div class="topbar">
    <h2 id="pageTitle">Dashboard</h2>
    <div class="topbar-actions">
      <button class="btn" onclick="refreshAll()">Refresh</button>
      <button class="btn" onclick="window.open('/api/docs','_blank')">API Docs</button>
    </div>
  </div>
  <div class="content">

    <!-- DASHBOARD -->
    <div class="page active" id="page-dashboard">
      <div class="kpi-row" id="kpiRow"></div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
        <div>
          <h3 style="font-size:14px;margin-bottom:10px">Jobs by Stage</h3>
          <div class="table-wrap" style="max-height:360px">
            <table class="data-table"><thead><tr><th>Stage</th><th>Count</th></tr></thead><tbody id="stageTable"></tbody></table>
          </div>
        </div>
        <div>
          <h3 style="font-size:14px;margin-bottom:10px">Recent Activity</h3>
          <div id="dashActivity" style="max-height:360px;overflow-y:auto"></div>
        </div>
      </div>
    </div>

    <!-- JOB BOARD -->
    <div class="page" id="page-board">
      <div class="board" id="jobBoard"></div>
    </div>

    <!-- APPROVALS -->
    <div class="page" id="page-approvals">
      <div class="table-wrap">
        <table class="data-table">
          <thead><tr><th>Task</th><th>Job</th><th>Stage</th><th>Priority</th><th>Reason</th><th>Amount</th><th>Action</th></tr></thead>
          <tbody id="approvalRows"></tbody>
        </table>
      </div>
    </div>

    <!-- VENDORS -->
    <div class="page" id="page-vendors">
      <div class="table-wrap">
        <table class="data-table">
          <thead><tr><th>Vendor</th><th>Code</th><th>Class</th><th>Status</th></tr></thead>
          <tbody id="vendorRows"></tbody>
        </table>
      </div>
    </div>

    <!-- ACTIVITY -->
    <div class="page" id="page-activity">
      <div id="activityList"></div>
    </div>

  </div>
</div>

<!-- Detail slide-over -->
<div class="detail-overlay" id="detailOverlay" onclick="if(event.target===this)closeDetail()">
  <div class="detail-panel" id="detailPanel"></div>
</div>

<script>
const API="/api";
const STAGES=[
  ["job_setup","Job Setup"],
  ["budget_review","Budget Review"],
  ["task_assignment","Task Assignment"],
  ["material_check","Material Check"],
  ["pricing_validation","Pricing / PO"],
  ["vendor_coordination","Vendor Coordination"],
  ["order_placement","Order Placement"],
  ["order_confirmation","Order Confirmation"],
  ["yard_pull","Yard Pull"],
  ["material_receiving","Material Receiving"],
  ["completion_check","Completion Check"],
  ["completed","Completed"]
];
const STAGE_LABELS=Object.fromEntries(STAGES);

let STATE={tasks:[],approvals:[],vendors:[],actions:[],summary:{}};

function headers(){return{"X-User-Email":document.getElementById("userEmail").value,"Content-Type":"application/json"}}
function money(v){return"$"+Number(v||0).toLocaleString(undefined,{maximumFractionDigits:0})}

async function api(path,opts={}){
  const res=await fetch(API+path,{headers:headers(),...opts});
  if(!res.ok){
    if(opts.allow403&&res.status===403)return null;
    console.warn(path,res.status);
    return null;
  }
  return res.json();
}

// Navigation
document.querySelectorAll(".nav-item").forEach(btn=>{
  btn.addEventListener("click",()=>{
    document.querySelectorAll(".nav-item").forEach(b=>b.classList.remove("active"));
    btn.classList.add("active");
    const pg=btn.dataset.page;
    document.querySelectorAll(".page").forEach(p=>p.classList.remove("active"));
    document.getElementById("page-"+pg).classList.add("active");
    document.getElementById("pageTitle").textContent=btn.querySelector("span:last-child").textContent;
  });
});

// ---- Data loading ----
async function loadAll(){
  const [summary,tasks,approvals,vendors,actions]=await Promise.all([
    api("/dashboard/summary"),
    api("/tasks?limit=500"),
    api("/approvals/financial?limit=200",{allow403:true}),
    api("/vendors?limit=500"),
    api("/workflow/actions/recent?limit=100"),
  ]);
  STATE.summary=summary||{};
  STATE.tasks=tasks||[];
  STATE.approvals=approvals||[];
  STATE.vendors=vendors||[];
  STATE.actions=actions||[];
  renderDashboard();
  renderBoard();
  renderApprovals();
  renderVendors();
  renderActivity();
}

// ---- Dashboard ----
function renderDashboard(){
  const s=STATE.summary;
  const kpis=[
    {label:"Open Jobs",value:s.open_tasks||0,color:"var(--accent)"},
    {label:"Awaiting Approval",value:s.financial_approvals_pending||0,color:"var(--amber)"},
    {label:"Invoice Exceptions",value:s.open_invoice_exceptions||0,color:"var(--red)"},
    {label:"Pending Confirmations",value:s.pending_order_confirmations||0,color:"var(--cyan)"},
    {label:"High Priority",value:s.open_high_priority_tasks||0,color:"var(--red)"},
    {label:"Tracked PO Spend",value:money(s.tracked_po_spend),color:"var(--green)"},
  ];
  document.getElementById("kpiRow").innerHTML=kpis.map(k=>`
    <div class="kpi">
      <div class="kpi-label">${k.label}</div>
      <div class="kpi-value" style="color:${k.color}">${k.value}</div>
    </div>`).join("");

  const stageCounts={};
  STATE.tasks.forEach(t=>{const st=t.workflow_stage||"unknown";stageCounts[st]=(stageCounts[st]||0)+1});
  document.getElementById("stageTable").innerHTML=STAGES.map(([key,label])=>{
    const n=stageCounts[key]||0;
    if(!n)return"";
    return`<tr><td>${label}</td><td>${n}</td></tr>`;
  }).join("")||"<tr><td colspan=2 class='empty-state'>No data</td></tr>";

  document.getElementById("dashActivity").innerHTML=(STATE.actions||[]).slice(0,15).map(a=>`
    <div class="activity-item">
      <div class="activity-dot ${a.action_mode}"></div>
      <div>
        <div class="activity-text"><strong>${a.action_type}</strong> on Task ${a.task_id||""}</div>
        <div class="activity-meta">${a.actor_email||"system"} &middot; ${a.action_mode}</div>
      </div>
    </div>`).join("")||"<div class='empty-state'>No recent activity</div>";
}

// ---- Job Board ----
function renderBoard(){
  const byStage={};
  STAGES.forEach(([k])=>byStage[k]=[]);
  STATE.tasks.forEach(t=>{
    const st=t.workflow_stage||"job_setup";
    if(!byStage[st])byStage[st]=[];
    byStage[st].push(t);
  });

  document.getElementById("jobBoard").innerHTML=STAGES.map(([key,label])=>{
    const items=byStage[key]||[];
    const cards=items.slice(0,30).map(t=>{
      const d=t.details||{};
      const pri=t.priority==="high"?"pill-high":"pill-normal";
      const mode=t.human_required?"pill-human":"pill-auto";
      return`<div class="card" onclick="openDetail(${t.id})">
        <div class="card-job">${t.job_number||"No Job #"}</div>
        <div class="card-vendor">${d.vendor||"Unknown vendor"}</div>
        <div class="card-row">
          <span class="pill ${pri}">${t.priority}</span>
          <span class="card-amount">${d.total!=null?money(d.total):""}</span>
        </div>
        <div class="card-row" style="margin-top:4px">
          <span class="pill ${mode}">${t.human_required?"Needs Approval":"Auto"}</span>
        </div>
      </div>`;
    }).join("");
    const overflow=items.length>30?`<div style="padding:6px;font-size:11px;color:var(--muted);text-align:center">+${items.length-30} more</div>`:"";
    return`<div class="lane">
      <div class="lane-header">
        <span class="lane-title">${label}</span>
        <span class="lane-count">${items.length}</span>
      </div>
      <div class="lane-body">${cards||"<div class='empty-state'>No items</div>"}${overflow}</div>
    </div>`;
  }).join("");
}

// ---- Detail panel ----
function openDetail(taskId){
  const t=STATE.tasks.find(x=>x.id===taskId);
  if(!t)return;
  const d=t.details||{};
  const stage=STAGE_LABELS[t.workflow_stage]||t.workflow_stage;
  const actions=getAvailableActions(t);

  document.getElementById("detailPanel").innerHTML=`
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
      <h3>Task #${t.id}</h3>
      <button class="btn btn-sm" onclick="closeDetail()">Close</button>
    </div>
    <div class="detail-field"><label>Job Number</label><div class="val">${t.job_number||"N/A"}</div></div>
    <div class="detail-field"><label>Current Stage</label><div class="val">${stage}</div></div>
    <div class="detail-field"><label>Status</label><div class="val"><span class="status-dot ${t.status==='completed'?'green':t.human_required?'amber':'blue'}"></span>${t.status}</div></div>
    <div class="detail-field"><label>Priority</label><div class="val">${t.priority}</div></div>
    <div class="detail-field"><label>Vendor</label><div class="val">${d.vendor||"N/A"}</div></div>
    <div class="detail-field"><label>PO Number</label><div class="val">${d.po_number||"N/A"}</div></div>
    <div class="detail-field"><label>Amount</label><div class="val">${d.total!=null?money(d.total):"N/A"}</div></div>
    <div class="detail-field"><label>Requires Human Action</label><div class="val">${t.human_required?"Yes":"No"}</div></div>
    <div class="detail-field"><label>Blocked Reason</label><div class="val">${t.blocked_reason||"None"}</div></div>
    <div class="detail-field"><label>Folder Path</label><div class="val" style="word-break:break-all;font-size:12px">${t.source_folder_path||"N/A"}</div></div>
    <div class="detail-actions">${actions}</div>`;
  document.getElementById("detailOverlay").classList.add("open");
}
function closeDetail(){document.getElementById("detailOverlay").classList.remove("open")}

function getAvailableActions(t){
  const st=t.workflow_stage;
  const btns=[];
  if(t.status==="completed")return"<span style='color:var(--green);font-size:13px'>&#10003; Completed</span>";

  const stageFlow={
    job_setup:       {next:"budget_review",   label:"Submit for Budget Review", style:"btn-primary"},
    budget_review:   {next:"task_assignment",  label:"Approve Budget",           style:"btn-green"},
    task_assignment: {next:"material_check",   label:"Assign Purchaser",         style:"btn-primary"},
    material_check:  {next:"pricing_validation",label:"Material Not Stocked - Need PO", style:"btn-amber"},
    pricing_validation:{next:"vendor_coordination",label:"Prices Need Update",   style:"btn-amber"},
    vendor_coordination:{next:"order_placement",label:"Coordination Complete",   style:"btn-green"},
    order_placement: {next:"order_confirmation",label:"Order Placed",            style:"btn-green"},
    order_confirmation:{next:"yard_pull",      label:"Confirmation Received",    style:"btn-green"},
    yard_pull:       {next:"material_receiving",label:"Yard Pull Generated",     style:"btn-primary"},
    material_receiving:{next:"completion_check",label:"Material Arrived",        style:"btn-green"},
    completion_check:{next:"completed",        label:"All Material Present",     style:"btn-green"},
  };

  const flow=stageFlow[st];
  if(flow){
    btns.push(`<button class="btn ${flow.style}" onclick="advanceTask(${t.id},'${flow.next}')">${flow.label}</button>`);
  }

  if(st==="material_check"){
    btns.push(`<button class="btn btn-green" onclick="advanceTask(${t.id},'yard_pull')">In Stock - Pull from Yard</button>`);
  }
  if(st==="completion_check"){
    btns.push(`<button class="btn btn-amber" onclick="advanceTask(${t.id},'vendor_coordination')">Missing Material - Reorder</button>`);
  }
  if(t.human_required){
    btns.push(`<button class="btn btn-green" onclick="approveTask(${t.id})">Approve (Financial)</button>`);
    btns.push(`<button class="btn btn-red" onclick="rejectTask(${t.id})">Reject</button>`);
  }
  return btns.join("");
}

async function advanceTask(taskId,nextStage){
  await api("/workflow/advance/"+taskId,{
    method:"POST",
    body:JSON.stringify({next_stage:nextStage}),
  });
  closeDetail();
  await loadAll();
}

async function approveTask(taskId){
  await api("/approvals/financial/"+taskId,{
    method:"POST",
    body:JSON.stringify({decision:"approve",notes:"Approved via platform"}),
  });
  closeDetail();
  await loadAll();
}

async function rejectTask(taskId){
  const reason=prompt("Rejection reason:");
  if(!reason)return;
  await api("/approvals/financial/"+taskId,{
    method:"POST",
    body:JSON.stringify({decision:"reject",notes:reason}),
  });
  closeDetail();
  await loadAll();
}

// ---- Approvals ----
function renderApprovals(){
  const rows=STATE.approvals||[];
  const badge=document.getElementById("approvalBadge");
  if(rows.length>0){badge.style.display="inline";badge.textContent=rows.length}
  else{badge.style.display="none"}
  document.getElementById("approvalRows").innerHTML=rows.map(r=>{
    const d=r.details||{};
    return`<tr>
      <td>${r.task_id}</td>
      <td>${r.job_number||""}</td>
      <td>${STAGE_LABELS[r.workflow_stage]||r.workflow_stage}</td>
      <td><span class="pill ${r.priority==='high'?'pill-high':'pill-normal'}">${r.priority}</span></td>
      <td style="max-width:200px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${r.blocked_reason||""}</td>
      <td>${d.total!=null?money(d.total):""}</td>
      <td>
        <button class="btn btn-sm btn-green" onclick="approveTask(${r.task_id})">Approve</button>
        <button class="btn btn-sm btn-red" onclick="rejectTask(${r.task_id})">Reject</button>
      </td>
    </tr>`;
  }).join("")||"<tr><td colspan=7 class='empty-state'>No pending approvals</td></tr>";
}

// ---- Vendors ----
function renderVendors(){
  document.getElementById("vendorRows").innerHTML=(STATE.vendors||[]).map(v=>`
    <tr>
      <td>${v.vendor_name||""}</td>
      <td>${v.vendor_code||""}</td>
      <td>${v.vendor_class||""}</td>
      <td>${v.vendor_status||""}</td>
    </tr>`).join("")||"<tr><td colspan=4 class='empty-state'>No vendors loaded</td></tr>";
}

// ---- Activity ----
function renderActivity(){
  document.getElementById("activityList").innerHTML=(STATE.actions||[]).map(a=>`
    <div class="activity-item">
      <div class="activity-dot ${a.action_mode}"></div>
      <div style="flex:1">
        <div class="activity-text"><strong>${a.action_type}</strong> &mdash; Task ${a.task_id||"N/A"}</div>
        <div class="activity-meta">${a.actor_email||"system"} &middot; ${a.action_mode} &middot; ${a.action_status}</div>
        ${a.notes?`<div class="activity-meta" style="margin-top:2px">${a.notes}</div>`:""}
      </div>
    </div>`).join("")||"<div class='empty-state'>No activity recorded</div>";
}

async function refreshAll(){await loadAll()}
loadAll();
setInterval(loadAll,30000);
</script>
</body>
</html>"""
