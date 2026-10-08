/*
 * 12123 Lovelace card
 *
 * The layout intentionally follows the visual language of the user's
 * pocket-carrier-card: a translucent rounded surface, a compact hero row,
 * blue accent pills and small information tiles.  It is self-contained so it
 * can be loaded as a single Home Assistant Lovelace resource.
 */
(function () {
  "use strict";

  // Custom element names must start with a letter; `12123-card` is rejected
  // by the browser before the card can even receive its configuration.
  const TAG = "ha-12123-card";
  const VERSION = "3.2.3";
  const ENTITY_FIELDS = ["user_entity", "driver_entity", "vehicle_entity", "violation_entity", "business_entity", "service_entity", "status_entity"];

  const DEFAULTS = {
    title: "12123",
    icon: "https://brands.home-assistant.io/12123/icon.png",
    theme: "light",
  };

  const CSS = `
    :host { display:block; }
    * { box-sizing:border-box; }
    ha-card.card, .card {
      width:100%; min-width:0;
      overflow:hidden;
      font-family:var(--paper-font-body1_-_font-family, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", PingFang SC, Microsoft YaHei, sans-serif);
      transition:box-shadow .25s ease,transform .25s ease;
    }

    /* 1. 浅色通透模式（纯正白玉质感，对齐掌上运营商） */
    ha-card.card.theme-light, .card.theme-light, .card:not(.theme-dark):not(.theme-auto) {
      --card-bg: var(--12123-card-background, rgba(255, 255, 255, 0.82));
      --card-border: var(--12123-card-border, rgba(0, 0, 0, 0.08));
      --card-radius: var(--12123-card-radius, 16px);
      --card-shadow: var(--12123-card-shadow, 0 8px 32px rgba(0, 0, 0, 0.1));
      --card-hover-shadow: var(--12123-card-hover-shadow, 0 12px 38px rgba(0, 0, 0, 0.15));
      --text-primary: #2c3e50;
      --text-secondary: #7f8c8d;
      --text-sub: #9e9e9e;
      --panel-bg: rgba(255, 255, 255, 0.65);
      --panel-border: rgba(0, 0, 0, 0.06);
      --panel-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
      --tab-bg: rgba(0, 0, 0, 0.04);
      --tab-hover-bg: rgba(33, 150, 243, 0.12);
      --tab-active-bg: rgba(33, 150, 243, 0.16);
      --tab-active-text: #1565c0;
      --tab-active-border: rgba(33, 150, 243, 0.25);
      --hero-bg: linear-gradient(135deg, rgba(33, 150, 243, 0.10), rgba(33, 150, 243, 0.02));
      --hero-border: rgba(33, 150, 243, 0.12);
      --dialog-bg: rgba(255, 255, 255, 0.98);

      color: var(--text-primary);
      background: var(--card-bg) !important;
      -webkit-backdrop-filter: blur(12px); backdrop-filter: blur(12px);
      border: 1px solid var(--card-border) !important;
      border-radius: var(--card-radius);
      box-shadow: var(--card-shadow) !important;
    }
    ha-card.card.theme-light:hover, .card.theme-light:hover { box-shadow: var(--card-hover-shadow) !important; }

    /* 2. 深色毛玻璃模式（纯正黑透毛玻璃，对齐奥迪车辆卡片） */
    ha-card.card.theme-dark, .card.theme-dark {
      --card-bg: var(--12123-card-background, rgba(30, 32, 38, 0.85));
      --card-border: var(--12123-card-border, rgba(255, 255, 255, 0.1));
      --card-radius: var(--12123-card-radius, 16px);
      --card-shadow: var(--12123-card-shadow, 0 8px 32px rgba(0, 0, 0, 0.4));
      --card-hover-shadow: var(--12123-card-hover-shadow, 0 12px 38px rgba(0, 0, 0, 0.5));
      --text-primary: rgba(255, 255, 255, 0.9);
      --text-secondary: rgba(255, 255, 255, 0.6);
      --text-sub: rgba(255, 255, 255, 0.4);
      --panel-bg: rgba(255, 255, 255, 0.06);
      --panel-border: rgba(255, 255, 255, 0.08);
      --panel-shadow: none;
      --tab-bg: rgba(255, 255, 255, 0.07);
      --tab-hover-bg: rgba(33, 150, 243, 0.2);
      --tab-active-bg: rgba(33, 150, 243, 0.25);
      --tab-active-text: #64b5f6;
      --tab-active-border: rgba(33, 150, 243, 0.35);
      --hero-bg: linear-gradient(135deg, rgba(33, 150, 243, 0.18), rgba(33, 150, 243, 0.04));
      --hero-border: rgba(255, 255, 255, 0.08);
      --dialog-bg: rgba(30, 32, 38, 0.98);

      color: var(--text-primary);
      background: var(--card-bg) !important;
      -webkit-backdrop-filter: blur(12px); backdrop-filter: blur(12px);
      border: 1px solid var(--card-border) !important;
      border-radius: var(--card-radius);
      box-shadow: var(--card-shadow) !important;
    }
    ha-card.card.theme-dark:hover, .card.theme-dark:hover { box-shadow: var(--card-hover-shadow) !important; }

    /* 3. 跟随系统/仪表盘（完全无任何自身背景，完全读取 HA 仪表盘主题） */
    ha-card.card.theme-auto, .card.theme-auto {
      --card-bg: var(--ha-card-background, var(--card-background-color, transparent));
      --card-border: var(--ha-card-border-color, var(--divider-color, transparent));
      --card-radius: var(--ha-card-border-radius, 16px);
      --card-shadow: var(--ha-card-box-shadow, none);
      --text-primary: var(--primary-text-color, inherit);
      --text-secondary: var(--secondary-text-color, inherit);
      --text-sub: var(--secondary-text-color, rgba(125, 125, 125, 0.7));
      --panel-bg: var(--ha-card-background, rgba(125, 125, 125, 0.08));
      --panel-border: var(--ha-card-border-color, var(--divider-color, rgba(125, 125, 125, 0.12)));
      --panel-shadow: none;
      --tab-bg: rgba(125, 125, 125, 0.08);
      --tab-hover-bg: rgba(33, 150, 243, 0.15);
      --tab-active-bg: rgba(33, 150, 243, 0.22);
      --tab-active-text: var(--primary-color, #2196f3);
      --tab-active-border: rgba(33, 150, 243, 0.35);
      --hero-bg: transparent;
      --hero-border: var(--ha-card-border-color, var(--divider-color, rgba(125, 125, 125, 0.12)));
      --dialog-bg: var(--ha-card-background, #ffffff);

      color: var(--text-primary);
      background: var(--card-bg);
      border: var(--ha-card-border-width, 1px) solid var(--card-border);
      border-radius: var(--card-radius);
      box-shadow: var(--card-shadow);
      -webkit-backdrop-filter: none;
      backdrop-filter: none;
    }

    .card.large .hero { gap:16px; padding:20px 22px 18px; }
    .card.large .hero-icon { width:58px; height:58px; border-radius:14px; padding:3px; }
    .card.large .title { font-size:24px; }
    .card.large .subtitle { margin-top:5px; font-size:13px; }
    .card.large .status { padding:5px 12px; font-size:12px; }
    .card.large .status::before { width:7px; height:7px; }
    .card.large .tabs { gap:8px; padding:12px 18px 2px; }
    .card.large .tab { padding:9px 16px; font-size:13px; }
    .card.large .content { padding:14px 18px 18px; }
    .card.large .tiles { gap:10px; }
    .card.large .tile { padding:13px 10px; border-radius:14px; }
    .card.large .tile-value { font-size:24px; }
    .card.large .tile-label { margin-top:5px; font-size:12px; }
    .card.large .section { margin-top:14px; }
    .card.large .section-title { font-size:14px; }
    .card.large .section-caption { font-size:12px; }
    .card.large .action-button { padding:6px 12px; font-size:12px; }
    .card.large .action-button ha-icon { --mdc-icon-size:15px; }
    .card.large .panel, .card.large .item { padding:13px 15px; border-radius:14px; }
    .card.large .kv-grid { gap:10px 16px; }
    .card.large .kv-label { font-size:12px; }
    .card.large .kv-value { font-size:13.5px; }
    .card.large .item-title { font-size:14px; }
    .card.large .meta { margin-top:8px; font-size:12px; }
    .card.large .violation-meta { font-size:12.5px; }
    .card.large .message-title { font-size:14px; }
    .card.large .message-body { font-size:12px; }
    .card.large .pagination { margin-top:14px; }
    .card.large .page-button { min-width:68px; padding:7px 13px; font-size:12px; }
    .card.large .page-indicator { font-size:12px; }
    .card.large .footer { padding-top:14px; font-size:12px; }

    .hero {
      display:flex; align-items:center; gap:12px; padding:15px 16px 13px;
      background:var(--hero-bg);
      border-bottom:1px solid var(--hero-border);
    }
    .hero-icon { width:44px; height:44px; flex:none; border-radius:12px; object-fit:cover; background:#fff; box-shadow:0 2px 6px rgba(0,0,0,0.06); padding:3px; }
    .hero-main { min-width:0; flex:1; }
    .title { color:var(--text-primary); font-size:20px; font-weight:700; line-height:1.2; letter-spacing:.1px; }
    .subtitle { color:var(--text-secondary); margin-top:4px; font-size:12px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .status { display:inline-flex; align-items:center; gap:5px; flex:none; border-radius:999px; padding:4px 10px; font-size:11px; font-weight:600; line-height:1; }
    .status::before { content:""; width:6px; height:6px; border-radius:50%; background:currentColor; box-shadow:0 0 0 3px color-mix(in srgb,currentColor 20%,transparent); }
    .status.online { color:#2e7d32; background:rgba(76,175,80,.14); }
    .status.offline { color:#c62828; background:rgba(244,67,54,.13); }
    .status.unknown { color:#78909c; background:rgba(120,144,156,.13); }

    .tabs { display:flex; gap:6px; padding:11px 14px 2px; overflow-x:auto; scrollbar-width:none; }
    .tabs::-webkit-scrollbar { display:none; }
    .tab { flex:1 0 auto; border:0; cursor:pointer; border-radius:999px; padding:6px 14px; color:var(--text-secondary); background:var(--tab-bg); font:inherit; font-size:12px; font-weight:500; line-height:1.2; transition:background .18s ease,color .18s ease; }
    .tab:hover { background:var(--tab-hover-bg); color:var(--tab-active-text); }
    .tab.active { color:var(--tab-active-text); background:var(--tab-active-bg); font-weight:650; box-shadow:inset 0 0 0 1px var(--tab-active-border); }

    .content { padding:12px 14px 14px; }
    .tiles { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:8px; }
    .tile { min-width:0; padding:10px 8px; border-radius:12px; background:var(--panel-bg); border:1px solid var(--panel-border); box-shadow:var(--panel-shadow); text-align:center; transition:transform .18s ease,box-shadow .18s ease,border-color .18s ease; }
    .tile-clickable { width:100%; border:0; color:inherit; cursor:pointer; font:inherit; }
    .tile-clickable:hover { border-color:rgba(33,150,243,.3); box-shadow:0 4px 12px rgba(33,150,243,.12); transform:translateY(-1px); }
    .tile-clickable:focus-visible { outline:2px solid #2196f3; outline-offset:2px; }
    .tile-value { font-size:20px; font-weight:700; line-height:1.2; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; font-family:Segoe UI,system-ui,-apple-system,BlinkMacSystemFont,sans-serif; font-variant-numeric:tabular-nums; color:var(--text-primary); }
    .tile-value.metric-score.safe { color:#2e7d32; }
    .tile-value.metric-score.warn { color:#e53935; }
    .tile-value.metric-vehicles { color:#1565c0; }
    .tile-value.metric-violations.safe { color:#2e7d32; }
    .tile-value.metric-violations.warn { color:#e53935; }
    .tile-value.metric-messages { color:#f57c00; }
    .tile-label { color:var(--text-secondary); margin-top:4px; font-size:11px; font-weight:500; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }

    .section { margin-top:12px; }
    .section-head { display:flex; align-items:center; justify-content:space-between; gap:8px; margin:0 2px 7px; }
    .section-title { color:var(--text-primary); font-size:13px; font-weight:650; display:flex; align-items:center; gap:6px; }
    .section-title::before { content:""; background:#2196f3; border-radius:2px; flex:none; width:3px; height:12px; }
    .section-caption { color:var(--text-sub); font-size:11px; }
    .section-actions { display:flex; align-items:center; gap:7px; }
    .action-button { display:inline-flex; align-items:center; gap:4px; color:#1565c0; border:0; border-radius:999px; padding:5px 10px; background:rgba(33,150,243,.13); cursor:pointer; font:inherit; font-size:11px; line-height:1.2; transition:background .18s ease,color .18s ease,opacity .18s ease; }
    .action-button:hover { color:#0d47a1; background:rgba(33,150,243,.24); }
    .action-button:disabled { cursor:wait; opacity:.62; }
    .action-button ha-icon { --mdc-icon-size:14px; }

    .panel { padding:12px 14px; border-radius:12px; background:var(--panel-bg); border:1px solid var(--panel-border); box-shadow:var(--panel-shadow); }
    .kv-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px 14px; }
    .kv { min-width:0; display:flex; flex-direction:column; gap:2px; }
    .kv-label { color:var(--text-secondary); font-size:11px; }
    .kv-value { color:var(--text-primary); font-weight:600; min-width:0; font-size:12.5px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }

    .list { display:flex; flex-direction:column; gap:8px; }
    .item { min-width:0; padding:11px 13px; border-radius:12px; background:var(--panel-bg); border:1px solid var(--panel-border); box-shadow:var(--panel-shadow); }
    .vehicle-button { display:block; width:100%; border:0; color:inherit; font:inherit; text-align:left; cursor:pointer; }
    .vehicle-button:hover { border-color:rgba(33,150,243,.3); box-shadow:0 4px 12px rgba(33,150,243,.12); }
    .vehicle-button:focus-visible { outline:2px solid #2196f3; outline-offset:2px; }
    .item-head { display:flex; align-items:center; gap:8px; }
    .item-icon { color:#1976d2; flex:none; --mdc-icon-size:18px; }
    .plate-icon { width:19px; height:19px; flex:none; color:#1976d2; }
    .item-title { min-width:0; flex:1; color:var(--text-primary); font-size:13px; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .item-badge { flex:none; color:#1565c0; background:rgba(33,150,243,.12); border-radius:999px; padding:2px 8px; font-size:10.5px; font-weight:500; }
    .meta { display:flex; flex-wrap:wrap; gap:5px 12px; margin-top:7px; color:var(--text-secondary); font-size:11px; }
    .violation-meta { flex-wrap:nowrap; gap:6px; overflow:hidden; white-space:nowrap; }
    .violation-meta > span { flex:none; }
    .meta span { min-width:0; }
    .meta strong { color:var(--text-primary); font-weight:550; }
    .meta .fine, .meta .fine strong { color:#e53935; }

    .message { cursor:default; }
    .message.unread { border-left:3px solid #2196f3; }
    .message-open { display:block; width:100%; padding:0; border:0; background:none; color:inherit; font:inherit; text-align:left; cursor:pointer; }
    .message-open:focus-visible { outline:2px solid #2196f3; outline-offset:3px; border-radius:4px; }
    .message-title { color:var(--text-primary); font-size:13px; font-weight:600; line-height:1.45; }
    .message-body { color:var(--text-secondary); margin-top:4px; font-size:11.5px; line-height:1.45; display:-webkit-box; -webkit-box-orient:vertical; -webkit-line-clamp:2; overflow:hidden; }

    .message-dialog { position:fixed; inset:0; margin:auto; width:min(520px,calc(100vw - 32px)); max-height:min(80vh,720px); padding:24px; border:1px solid rgba(0,0,0,.08); border-radius:20px; background:#ffffff !important; background-color:#ffffff !important; color:#2c3e50; box-shadow:0 24px 60px rgba(0,0,0,.28), 0 4px 16px rgba(0,0,0,.08); overflow:auto; box-sizing:border-box; font-family:var(--paper-font-body1_-_font-family, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", PingFang SC, Microsoft YaHei, sans-serif); }
    .message-dialog::backdrop { background:rgba(0,0,0,.65); -webkit-backdrop-filter:blur(8px); backdrop-filter:blur(8px); }
    .message-dialog .dialog-head { display:flex; align-items:flex-start; justify-content:space-between; gap:12px; }
    .message-dialog .dialog-title { margin:0; font-size:18px; font-weight:700; line-height:1.4; color:#2c3e50; }
    .message-dialog .dialog-close { flex:none; display:grid; place-items:center; width:32px; height:32px; padding:0; border:0; border-radius:50%; background:rgba(0,0,0,.06); color:#7f8c8d; font:inherit; font-size:20px; line-height:1; cursor:pointer; transition:background .18s ease,color .18s ease; }
    .message-dialog .dialog-close:hover { background:rgba(0,0,0,.12); color:#2c3e50; }
    .message-dialog .dialog-close:focus-visible { outline:2px solid #2196f3; outline-offset:2px; }
    .message-dialog .dialog-category { display:inline-block; margin-top:10px; padding:4px 10px; border-radius:999px; background:rgba(33,150,243,.12); color:#1565c0; font-size:11.5px; font-weight:600; }
    .message-dialog .dialog-body { margin:16px 0 0; white-space:pre-wrap; overflow-wrap:anywhere; line-height:1.7; font-size:13.5px; color:#34495e; }
    .message-dialog .dialog-date { margin-top:16px; color:#7f8c8d; font-size:11.5px; }

    .message-dialog.theme-dark { border:1px solid rgba(255,255,255,.12); background:#1e2026 !important; background-color:#1e2026 !important; color:rgba(255,255,255,.95); box-shadow:0 24px 60px rgba(0,0,0,.75), 0 4px 16px rgba(0,0,0,.5); }
    .message-dialog.theme-dark::backdrop { background:rgba(0,0,0,.75); -webkit-backdrop-filter:blur(8px); backdrop-filter:blur(8px); }
    .message-dialog.theme-dark .dialog-title { color:rgba(255,255,255,.95); }
    .message-dialog.theme-dark .dialog-close { background:rgba(255,255,255,.12); color:rgba(255,255,255,.75); }
    .message-dialog.theme-dark .dialog-close:hover { background:rgba(255,255,255,.22); color:#ffffff; }
    .message-dialog.theme-dark .dialog-category { background:rgba(33,150,243,.25); color:#64b5f6; }
    .message-dialog.theme-dark .dialog-body { color:rgba(255,255,255,.88); }
    .message-dialog.theme-dark .dialog-date { color:rgba(255,255,255,.5); }

    .message-filter { display:flex; gap:6px; margin:0 2px 9px; overflow-x:auto; scrollbar-width:none; }
    .message-filter::-webkit-scrollbar { display:none; }
    .message-filter-button { flex:1 0 auto; color:var(--text-secondary); border:0; border-radius:999px; padding:6px 12px; background:var(--tab-bg); cursor:pointer; font:inherit; font-size:11px; line-height:1.2; transition:background .18s ease,color .18s ease; }
    .message-filter-button:hover { color:var(--tab-active-text); background:var(--tab-hover-bg); }
    .message-filter-button.active { color:var(--tab-active-text); background:var(--tab-active-bg); box-shadow:inset 0 0 0 1px var(--tab-active-border); font-weight:650; }

    .pagination { display:flex; align-items:center; justify-content:center; gap:8px; margin-top:12px; }
    .page-button { min-width:58px; color:#1565c0; border:0; border-radius:999px; padding:6px 10px; background:rgba(33,150,243,.12); cursor:pointer; font:inherit; font-size:11px; transition:background .18s ease,color .18s ease,opacity .18s ease; }
    .page-button:hover { color:#0d47a1; background:rgba(33,150,243,.22); }
    .page-button:disabled { color:var(--text-sub); cursor:default; opacity:.5; background:var(--tab-bg); }
    .page-indicator { color:var(--text-secondary); min-width:44px; text-align:center; font-size:11px; }

    .photos { display:flex; gap:6px; overflow-x:auto; margin-top:8px; padding-bottom:1px; }
    .photos img { width:78px; height:58px; flex:none; border-radius:7px; object-fit:cover; background:rgba(0,0,0,.06); cursor:pointer; }
    .photos a { display:block; }
    .empty { color:var(--text-sub); display:flex; align-items:center; justify-content:center; gap:7px; min-height:54px; font-size:12px; }
    .error { color:#c62828; padding:16px; font-size:12px; line-height:1.5; }
    .footer { display:flex; justify-content:space-between; gap:8px; padding-top:12px; margin-top:8px; border-top:1px solid var(--panel-border); color:var(--text-sub); font-size:11px; }
    .footer span { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    .footer-status { min-width:0; flex:1; }

    @media (max-width:520px) {
      .hero { padding:13px 14px 11px; }
      .content { padding:10px 11px 13px; }
      .tiles { grid-template-columns:repeat(2,minmax(0,1fr)); }
      .kv-grid { grid-template-columns:1fr; }
    }
  `;

  class Jiaoguan12123Card extends HTMLElement {
    static getConfigForm() {
      const entitySelector = { entity: { filter: [{ integration: "12123", domain: "sensor" }, { integration: "shaobo_12123", domain: "sensor" }] } };
      const labels = {
        title: "卡片名称",
        size: "卡片尺寸",
        theme: "卡片主题风格",
        user_entity: "用户信息实体",
        driver_entity: "驾驶证信息实体",
        vehicle_entity: "车辆信息实体",
        violation_entity: "车辆违章实体",
        business_entity: "业务告知实体",
        service_entity: "服务提醒实体",
        status_entity: "在线状态实体",
      };
      return {
        schema: [
          { name: "title", selector: { text: {} } },
          { name: "size", selector: { select: { options: [
            { value: "large", label: "大尺寸" },
            { value: "normal", label: "标准尺寸" },
          ], mode: "dropdown" } } },
          { name: "theme", selector: { select: { options: [
            { value: "light", label: "浅色通透（默认，对齐掌上运营商）" },
            { value: "dark", label: "深色毛玻璃" },
            { value: "auto", label: "跟随系统 / 仪表盘" },
          ], mode: "dropdown" } } },
          ...ENTITY_FIELDS.map((name) => ({ name, selector: entitySelector })),
        ],
        computeLabel: (schema) => labels[schema.name],
      };
    }

    static getStubConfig() {
      return {
        title: DEFAULTS.title,
        size: "large",
        theme: "light",
      };
    }

    constructor() {
      super();
      this.attachShadow({ mode: "open" });
      this._hass = null;
      this._config = null;
      this._tab = "overview";
      this._messagePage = 1;
      this._messageCategory = "all";
      this._visibleMessages = [];
      this._openMessage = null;
      this._metaResizeObserver = null;
      this._lastCardWidth = 0;
      this._signature = "";
      this._onClick = (event) => this._handleClick(event);
    }

    setConfig(config) {
      if (!config || typeof config !== "object") {
        throw new Error("12123 卡片配置无效");
      }
      this._config = { ...DEFAULTS, ...config };
      this._tab = this._loadTab();
      this._messageCategory = this._loadMessageCategory();
      this._signature = "";
      if (this._hass) this._render();
    }

    set hass(hass) {
      this._hass = hass;
      if (!this._config) return;
      const signature = this._makeSignature();
      if (signature !== this._signature) {
        this._signature = signature;
        this._render();
      }
    }

    get hass() { return this._hass; }

    connectedCallback() {
      this.shadowRoot.addEventListener("click", this._onClick);
      if (this._hass && this._config) this._render();
      if (!this._themeMediaHandler && typeof window !== "undefined" && window.matchMedia) {
        this._themeMedia = window.matchMedia("(prefers-color-scheme: dark)");
        this._themeMediaHandler = () => {
          if (this._config?.theme === "auto") {
            this._signature = "";
            this._render();
          }
        };
        try {
          this._themeMedia.addEventListener("change", this._themeMediaHandler);
        } catch (_) {
          this._themeMedia.addListener?.(this._themeMediaHandler);
        }
      }
      if (!this._themeEventHandler && typeof window !== "undefined") {
        this._themeEventHandler = () => {
          if (this._config?.theme === "auto") {
            this._signature = "";
            this._render();
          }
        };
        window.addEventListener("settheme", this._themeEventHandler);
        window.addEventListener("themes-updated", this._themeEventHandler);
        window.addEventListener("hass-theme-changed", this._themeEventHandler);
      }
    }

    disconnectedCallback() {
      this.shadowRoot.removeEventListener("click", this._onClick);
      this._metaResizeObserver?.disconnect();
      this._metaResizeObserver = null;
      if (this._themeMedia && this._themeMediaHandler) {
        try {
          this._themeMedia.removeEventListener("change", this._themeMediaHandler);
        } catch (_) {
          this._themeMedia.removeListener?.(this._themeMediaHandler);
        }
        this._themeMediaHandler = null;
      }
      if (this._themeEventHandler && typeof window !== "undefined") {
        window.removeEventListener("settheme", this._themeEventHandler);
        window.removeEventListener("themes-updated", this._themeEventHandler);
        window.removeEventListener("hass-theme-changed", this._themeEventHandler);
        this._themeEventHandler = null;
      }
    }

    getCardSize() { return 6; }

    _isColorLight(color) {
      if (!color) return false;
      color = String(color).trim();
      let r = 0, g = 0, b = 0;
      if (color.startsWith("#")) {
        const hex = color.slice(1);
        if (hex.length === 3) {
          r = parseInt(hex[0] + hex[0], 16) || 0;
          g = parseInt(hex[1] + hex[1], 16) || 0;
          b = parseInt(hex[2] + hex[2], 16) || 0;
        } else if (hex.length >= 6) {
          r = parseInt(hex.slice(0, 2), 16) || 0;
          g = parseInt(hex.slice(2, 4), 16) || 0;
          b = parseInt(hex.slice(4, 6), 16) || 0;
        }
      } else if (color.includes("(")) {
        const parts = color.match(/[\d.]+/g);
        if (parts && parts.length >= 3) {
          r = parseFloat(parts[0]) || 0;
          g = parseFloat(parts[1]) || 0;
          b = parseFloat(parts[2]) || 0;
        }
      } else {
        return false;
      }
      return (r * 299 + g * 587 + b * 114) / 1000 > 130;
    }

    _isDarkMode() {
      const mode = this._config?.theme || "light";
      if (mode === "dark") return true;
      if (mode === "light") return false;

      // 1. Home Assistant 的核心状态检测
      if (this._hass) {
        if (this._hass.themes?.darkMode === true) return true;
        if (this._hass.themes?.darkMode === false) return false;
        const selectedTheme = String(this._hass.selectedTheme || this._hass.themes?.theme || "").toLowerCase();
        if (selectedTheme.includes("dark") || selectedTheme.includes("night") || selectedTheme.includes("black")) {
          return true;
        }
      }

      // 2. Home Assistant DOM 树属性检测
      if (typeof document !== "undefined") {
        if (document.documentElement.classList.contains("dark") || document.documentElement.getAttribute("data-theme") === "dark") return true;
        if (document.body && (document.body.classList.contains("dark") || document.body.getAttribute("data-theme") === "dark")) return true;
        const ha = document.querySelector("home-assistant");
        if (ha && (ha.hasAttribute("dark") || ha.classList.contains("dark"))) return true;
      }

      // 3. 从宿主或全局计算样式检测当前主题的文字和背景颜色
      try {
        const host = this.shadowRoot?.host || this;
        if (host && typeof window !== "undefined" && window.getComputedStyle) {
          const style = window.getComputedStyle(host);
          const textColor = style.getPropertyValue("--primary-text-color").trim();
          if (textColor && this._isColorLight(textColor)) return true;
          const cardBg = style.getPropertyValue("--ha-card-background").trim();
          if (cardBg && !this._isColorLight(cardBg)) return true;
        }
      } catch (_) {}

      // 4. 系统级 prefers-color-scheme 检测
      if (typeof window !== "undefined" && window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
        return true;
      }
      return false;
    }

    _getThemeClass() {
      return this._isDarkMode() ? "theme-dark" : "theme-light";
    }

    _state(entityId) {
      return (this._hass && this._hass.states && this._hass.states[entityId]) || { state: "unknown", attributes: {} };
    }

    _attrs(entityId) { return this._state(entityId).attributes || {}; }

    _makeSignature() {
      if (!this._hass || !this._config) return "";
      const isDark = this._isDarkMode();
      const themeConfig = this._config.theme || "auto";
      const haDark = this._hass.themes?.darkMode ?? "";
      const haTheme = this._hass.selectedTheme || this._hass.themes?.theme || "";
      const entitySig = ENTITY_FIELDS.map((key) => {
        const state = this._state(this._config[key]);
        return `${this._config[key]}:${state.state}:${state.last_changed || ""}:${state.last_updated || ""}`;
      }).join("|");
      return `${entitySig}#theme:${themeConfig}:${isDark ? "dark" : "light"}:${haDark}:${haTheme}`;
    }

    _data() {
      const cfg = this._config;
      const userState = this._state(cfg.user_entity);
      const driverState = this._state(cfg.driver_entity);
      const vehicleState = this._state(cfg.vehicle_entity);
      const violationState = this._state(cfg.violation_entity);
      const businessState = this._state(cfg.business_entity);
      const serviceState = this._state(cfg.service_entity);
      const statusState = this._state(cfg.status_entity);
      const user = this._attrs(cfg.user_entity).user_info || {};
      const driver = this._attrs(cfg.driver_entity).driver_info || {};
      const vehicles = this._asArray(this._attrs(cfg.vehicle_entity).vehicles);
      const violations = this._asArray(this._attrs(cfg.violation_entity).vehicle_violations);
      const business = this._asArray(this._attrs(cfg.business_entity).messages);
      const service = this._asArray(this._attrs(cfg.service_entity).messages);
      return { userState, driverState, vehicleState, violationState, businessState, serviceState, statusState, user, driver, vehicles, violations, business, service };
    }

    _render() {
      if (!this.shadowRoot || !this._config || !this._hass) return;
      this._metaResizeObserver?.disconnect();
      this._metaResizeObserver = null;
      const data = this._data();
      const root = document.createElement("div");
      root.innerHTML = `<style>${CSS}</style>`;
      const card = document.createElement("ha-card");
      const sizeClass = this._config.size === "large" ? " large" : "";
      const themeMode = this._config.theme || "light";
      card.className = `card${sizeClass} theme-${themeMode}`;
      card.innerHTML = ENTITY_FIELDS.some((key) => this._config[key])
        ? this._renderHero(data) + this._renderTabs() + `<div class="content">${this._renderTabContent(data)}${this._renderFooter(data)}</div>`
        : `<div class="content"><div class="empty">请在卡片配置中选择 12123 传感器实体</div></div>`;
      root.appendChild(card);
      this.shadowRoot.replaceChildren(root);
      this._fitViolationMeta(card);
      if (typeof ResizeObserver !== "undefined" && card.querySelector(".violation-meta")) {
        this._lastCardWidth = card.clientWidth;
        this._metaResizeObserver = new ResizeObserver(() => {
          if (card.clientWidth === this._lastCardWidth) return;
          this._lastCardWidth = card.clientWidth;
          this._fitViolationMeta(card);
        });
        this._metaResizeObserver.observe(card);
      }
      if (this._openMessage) this._showMessageDialog();
    }

    _fitViolationMeta(card) {
      const maximum = card.classList.contains("large") ? 13 : 11;
      for (const meta of card.querySelectorAll(".violation-meta")) {
        if (!meta.clientWidth) continue;
        meta.style.flexWrap = "nowrap";
        for (let size = maximum; size >= 10; size -= 0.5) {
          meta.style.fontSize = `${size}px`;
          if (meta.scrollWidth <= meta.clientWidth + 1) break;
        }
        if (meta.scrollWidth > meta.clientWidth + 1) meta.style.flexWrap = "wrap";
      }
    }

    _renderHero(data) {
      const name = this._text(data.user.xm || data.driver.xm || data.userState.state || "用户");
      const rawStatus = String(data.statusState.state || "unknown");
      const statusClass = rawStatus === "在线" || rawStatus.toLowerCase() === "online" ? "online" : rawStatus === "离线" || rawStatus.toLowerCase() === "offline" ? "offline" : "unknown";
      const statusLabel = statusClass === "online" ? "在线" : statusClass === "offline" ? "离线" : "状态未知";
      const icon = this._attr(this._config.icon || DEFAULTS.icon);
      return `<div class="hero"><img class="hero-icon" src="${icon}" alt="12123" loading="lazy" referrerpolicy="no-referrer"><div class="hero-main"><div class="title">${this._text(this._config.title || DEFAULTS.title)}</div><div class="subtitle">${name}${data.user.sfzmhm ? ` · ${this._text(data.user.sfzmhm)}` : ""}</div></div><span class="status ${statusClass}">${statusLabel}</span></div>`;
    }

    _renderTabs() {
      const tabs = [["overview", "总览"], ["vehicles", "车辆"], ["violations", "违章"], ["messages", "消息"]];
      return `<nav class="tabs" aria-label="12123 内容分类">${tabs.map(([key, label]) => `<button class="tab ${this._tab === key ? "active" : ""}" data-tab="${key}">${label}</button>`).join("")}</nav>`;
    }

    _renderTabContent(data) {
      if (this._tab === "vehicles") return this._renderVehicles(data);
      if (this._tab === "violations") return this._renderViolations(data);
      if (this._tab === "messages") return this._renderMessages(data);
      return this._renderOverview(data);
    }

    _renderOverview(data) {
      const driverScore = data.driver.ljjf ?? data.driver.cumulative_score ?? data.driverState.state ?? "0";
      const violationCount = data.violationState.state === "unknown" ? (data.violations.length || 0) : data.violationState.state;
      const businessCount = data.businessState.state === "unknown" ? data.business.length : data.businessState.state;
      const serviceCount = data.serviceState.state === "unknown" ? data.service.length : data.serviceState.state;
      const totalMessages = Number(businessCount || 0) + Number(serviceCount || 0);

      const scoreNum = Number(driverScore);
      const scoreClass = scoreNum > 0 ? "warn" : "safe";
      const violNum = Number(violationCount);
      const violClass = violNum > 0 ? "warn" : "safe";

      const driverPanel = this._renderKvPanel("驾驶证信息", [
        ["姓名", data.driver.xm], ["准驾车型", data.driver.zjcx], ["累计记分", this._withUnit(driverScore, "分")], ["状态", data.driver.ztStr], ["有效期至", data.driver.yxqz], ["下次清分日期", data.driver.qfrq],
      ]);
      const userPanel = this._renderKvPanel("用户信息", [
        ["姓名", data.user.xm], ["身份证号", data.user.sfzmhm], ["手机号", data.user.sjhm], ["性别", data.user.xb], ["所在地区", data.user.csmc], ["账号状态", data.user.zt === "1" ? "正常" : data.user.zt],
      ]);
      return `<div class="tiles"><button class="tile tile-clickable" type="button" data-tab="overview"><div class="tile-value metric-score ${scoreClass}">${this._text(driverScore)}</div><div class="tile-label">累计记分</div></button><button class="tile tile-clickable" type="button" data-tab="vehicles"><div class="tile-value metric-vehicles">${this._text(data.vehicles.length || data.vehicleState.state)}</div><div class="tile-label">车辆</div></button><button class="tile tile-clickable" type="button" data-tab="violations"><div class="tile-value metric-violations ${violClass}">${this._text(violationCount)}</div><div class="tile-label">未处理违章</div></button><button class="tile tile-clickable" type="button" data-tab="messages"><div class="tile-value metric-messages">${this._text(totalMessages)}</div><div class="tile-label">消息</div></button></div><div class="section">${driverPanel}</div><div class="section">${userPanel}</div>`;
    }

    _renderVehicles(data) {
      if (!data.vehicles.length) return this._empty("暂无车辆信息");
      return `<div class="section-head"><span class="section-title">车辆信息</span><span class="section-caption">${data.vehicles.length} 辆</span></div><div class="list">${data.vehicles.map((vehicle, index) => {
        const plate = vehicle.hphm || vehicle.plate_number || "未知车牌";
        const status = vehicle.ztStr || vehicle.status || "";
        const hasViolations = this._vehicleHasViolations(vehicle, data.violations);
        const start = hasViolations
          ? `<button class="item vehicle-button" type="button" data-action="vehicle-violations" data-vehicle-index="${index}" aria-label="查看 ${this._attr(plate)} 的违章">`
          : `<article class="item">`;
        const end = hasViolations ? "</button>" : "</article>";
        return `${start}<span class="item-head"><ha-icon class="item-icon" icon="mdi:car"></ha-icon><span class="item-title">${this._text(plate)}</span>${status ? `<span class="item-badge">${this._text(status)}</span>` : ""}</span><span class="meta"><span>类型：<strong>${this._text(vehicle.hpzlStr || vehicle.hpzl || "-")}</strong></span><span>未处理：<strong>${this._text(vehicle.wfsl ?? 0)} 条</strong></span>${vehicle.yxqz ? `<span>年检至：<strong>${this._text(vehicle.yxqz)}</strong></span>` : ""}<span>交强险至：<strong>${this._text(vehicle.jqxzzrq || "暂无数据")}</strong></span></span>${end}`;
      }).join("")}</div>`;
    }

    _vehicleHasViolations(vehicle, violations) {
      if (Number(vehicle.wfsl) > 0) return true;
      const plate = vehicle.hphm || vehicle.plate_number;
      const match = this._asArray(violations).find((item) => (item.hphm || item.plate_number) === plate);
      return !!match && Number(match.violation_count ?? this._asArray(match.violations).length) > 0;
    }

    _renderViolations(data) {
      const count = data.violationState.state === "unknown" ? data.violations.length : data.violationState.state;
      const refreshLabel = this._refreshingViolations ? "更新中…" : "更新违章图片";
      const content = data.violations.length
        ? `<div class="list">${data.violations.map((vehicle) => this._renderViolationVehicle(vehicle)).join("")}</div>`
        : this._empty("暂无车辆违章");
      return `<div class="section-head"><span class="section-title">车辆违章</span><div class="section-actions"><span class="section-caption">${this._text(count)} 条</span><button class="action-button" type="button" data-action="refresh-violations" ${this._refreshingViolations ? "disabled" : ""}><ha-icon icon="mdi:image-refresh-outline"></ha-icon><span>${refreshLabel}</span></button></div></div>${content}`;
    }

    _renderViolationVehicle(vehicle) {
      const plate = vehicle.hphm || vehicle.plate_number || "未知车牌";
      const list = this._asArray(vehicle.violations || vehicle.list || vehicle.items);
      const direct = list.length ? "" : this._renderViolation(vehicle);
      const icon = `<svg class="plate-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M5 11.5 6.7 6h10.6l1.7 5.5H20a1 1 0 0 1 1 1V18a1 1 0 0 1-1 1h-1v1.5h-2V19H7v1.5H5V19H4a1 1 0 0 1-1-1v-5.5a1 1 0 0 1 1-1h1Zm3.2-3.5-1 3h9.6l-1-3H8.2ZM6.5 15a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3Zm11 0a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3ZM6 13h12v1H6v-1Z"/></svg>`;
      return `<article class="item" data-violation-plate="${this._attr(plate)}"><div class="item-head">${icon}<div class="item-title">${this._text(plate)}</div><span class="item-badge">${this._text(vehicle.violation_count ?? list.length ?? 0)} 条</span></div>${list.length ? `<div class="list" style="margin-top:8px">${list.map((item) => this._renderViolation(item)).join("")}</div>` : direct}</article>`;
    }

    _renderViolation(item) {
      if (!item || typeof item !== "object") return "";
      const title = item.wfms || item.wfact || item.wfxw || "违法记录";
      const address = item.wfdz || item.wfdd || "";
      const date = item.wfsj || item.time || "";
      const photoSource = this._asArray(item.local_photos).length ? item.local_photos : item.photos;
      const photos = this._asArray(photoSource).filter((photo) => typeof photo === "string" && (/^https?:\/\//i.test(photo) || photo.startsWith("/local/") || photo.startsWith("/12123-images/")));

      return `<div class="message"><div class="message-title">${this._text(title)}</div><div class="meta violation-meta">${date ? `<span>时间：<strong>${this._text(date)}</strong></span>` : ""}${address ? `<span>地点：<strong>${this._text(address)}</strong></span>` : ""}${item.fkje !== undefined ? `<span class="fine">罚款：<strong>${this._text(item.fkje)} 元</strong></span>` : ""}${item.wfjfs !== undefined ? `<span>记分：<strong>${this._text(item.wfjfs)} 分</strong></span>` : ""}</div>${photos.length ? `<div class="photos">${photos.map((photo, index) => `<a href="${this._attr(photo)}" target="_blank" rel="noreferrer"><img src="${this._attr(photo)}" alt="违章照片 ${index + 1}" loading="lazy" referrerpolicy="no-referrer"></a>`).join("")}</div>` : ""}</div>`;
    }

    _renderMessages(data) {
      const business = data.business.map((item) => ({ ...item, _category: "业务告知" }));
      const service = data.service.map((item) => ({ ...item, _category: "服务提醒" }));
      const all = this._messageCategory === "business"
        ? business
        : this._messageCategory === "service" ? service : [...business, ...service];
      const pageSize = 10;
      const pageCount = Math.max(1, Math.ceil(all.length / pageSize));
      this._messagePage = Math.min(Math.max(Number(this._messagePage) || 1, 1), pageCount);
      const start = (this._messagePage - 1) * pageSize;
      const visible = all.slice(start, start + pageSize);
      this._visibleMessages = visible;
      const list = visible.length
        ? `<div class="list">${visible.map((item, index) => this._renderMessage(item, index)).join("")}</div>`
        : this._empty("暂无消息");
      const pagination = pageCount > 1
        ? `<div class="pagination"><button class="page-button" type="button" data-action="message-prev" ${this._messagePage <= 1 ? "disabled" : ""}>上一页</button><span class="page-indicator">${this._messagePage} / ${pageCount}</span><button class="page-button" type="button" data-action="message-next" ${this._messagePage >= pageCount ? "disabled" : ""}>下一页</button></div>`
        : "";
      const filter = [["all", "全部"], ["business", "业务告知"], ["service", "服务提醒"]]
        .map(([key, label]) => `<button class="message-filter-button ${this._messageCategory === key ? "active" : ""}" type="button" data-action="message-filter" data-message-category="${key}">${label}</button>`)
        .join("");
      return `<div class="section-head"><span class="section-title">消息中心</span><span class="section-caption">${all.length} 条</span></div><div class="message-filter" role="tablist" aria-label="消息类型">${filter}</div>${list}${pagination}`;
    }

    _renderMessage(item, index) {
      const title = item.title || item.bt || item.xxbt || item.name || item._category;
      const body = item.content || item.nr || item.xxnr || item.description || "";
      const date = item.time || item.fssj || item.create_time || item.date || "";
      const unread = item.read === false || item.sfyd === "0";
      return `<article class="item message ${unread ? "unread" : ""}"><button class="message-open" type="button" data-action="open-message" data-message-index="${index}" aria-label="查看完整消息：${this._attr(title)}"><span class="item-head"><ha-icon class="item-icon" icon="mdi:message-text-outline"></ha-icon><span class="item-title">${this._text(title)}</span><span class="item-badge">${this._text(item._category)}</span></span>${body ? `<span class="message-body">${this._text(body)}</span>` : ""}${date ? `<span class="meta"><span>${this._text(date)}</span></span>` : ""}</button></article>`;
    }

    _showMessageDialog() {
      const item = this._openMessage;
      const title = item.title || item.bt || item.xxbt || item.name || item._category;
      const body = item.content || item.nr || item.xxnr || item.description || "";
      const date = item.time || item.fssj || item.create_time || item.date || "";
      const dialog = document.createElement("dialog");
      const isDark = this._config?.theme === "dark" || (this._config?.theme === "auto" && this._isDarkMode());
      dialog.className = `message-dialog ${isDark ? "theme-dark" : "theme-light"}`;
      dialog.setAttribute("aria-labelledby", "message-dialog-title");
      dialog.innerHTML = `<div class="dialog-head"><h2 class="dialog-title" id="message-dialog-title">${this._text(title)}</h2><button class="dialog-close" type="button" data-action="close-message" aria-label="关闭消息">×</button></div><span class="dialog-category">${this._text(item._category)}</span>${body ? `<p class="dialog-body">${this._text(body)}</p>` : ""}${date ? `<div class="dialog-date">${this._text(date)}</div>` : ""}`;
      dialog.addEventListener("close", () => { this._openMessage = null; dialog.remove(); });
      dialog.addEventListener("click", (event) => {
        if (event.target !== dialog) return;
        const bounds = dialog.getBoundingClientRect();
        if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
      });
      this.shadowRoot.appendChild(dialog);
      dialog.showModal();
    }

    _renderKvPanel(title, entries) {
      const visible = entries.filter(([, value]) => value !== undefined && value !== null && String(value) !== "");
      return `<div class="section-head"><span class="section-title">${this._text(title)}</span></div><div class="panel"><div class="kv-grid">${(visible.length ? visible : [["信息", "暂无"]]).map(([label, value]) => `<div class="kv"><span class="kv-label">${this._text(label)}</span><span class="kv-value">${this._text(value)}</span></div>`).join("")}</div></div>`;
    }

    _renderFooter(data) {
      const statusAttrs = data.statusState.attributes || {};
      const last = statusAttrs["数据更新时间"] || data.statusState.last_updated || data.violationState.last_updated || "";
      const interval = Number(statusAttrs["数据刷新间隔"]);
      const refreshText = Number.isFinite(interval) && interval > 0 ? ` · ${interval}分钟自动更新` : "";
      const ver = statusAttrs["version"] || statusAttrs["版本"] || VERSION;
      const displayVer = String(ver).startsWith("v") ? String(ver) : `v${ver}`;
      const label = last
        ? `数据更新 ${this._formatDate(last)}${refreshText}`
        : "数据由 12123 后端提供";
      return `<div class="footer"><span class="footer-status">${this._text(label)}</span><span>${this._text(displayVer)}</span></div>`;
    }


    _handleClick(event) {
      const action = event.target.closest && event.target.closest("[data-action]");
      if (action) {
        const actionName = action.getAttribute("data-action");
        if (actionName === "vehicle-violations") {
          const index = Number(action.getAttribute("data-vehicle-index"));
          const data = this._data();
          const vehicle = Number.isInteger(index) ? data.vehicles[index] : null;
          if (!vehicle || !this._vehicleHasViolations(vehicle, data.violations)) return;
          const plate = vehicle.hphm || vehicle.plate_number || "未知车牌";
          this._tab = "violations";
          this._saveTab(this._tab);
          this._render();
          const target = [...this.shadowRoot.querySelectorAll("[data-violation-plate]")]
            .find((item) => item.getAttribute("data-violation-plate") === plate);
          target?.scrollIntoView({ block: "center" });
          return;
        }
        if (actionName === "open-message") {
          const index = Number(action.getAttribute("data-message-index"));
          if (Number.isInteger(index) && this._visibleMessages[index]) {
            this._openMessage = this._visibleMessages[index];
            this._showMessageDialog();
          }
          return;
        }
        if (actionName === "close-message") {
          this.shadowRoot.querySelector(".message-dialog")?.close();
          return;
        }
        if (actionName === "refresh-violations") {
          this._refreshViolations();
          return;
        }
        if (actionName === "message-prev" || actionName === "message-next") {
          this._messagePage += actionName === "message-next" ? 1 : -1;
          this._render();
          return;
        }
        if (actionName === "message-filter") {
          const category = action.getAttribute("data-message-category");
          if (["all", "business", "service"].includes(category)) {
            this._messageCategory = category;
            this._messagePage = 1;
            this._saveMessageCategory(category);
            this._render();
          }
          return;
        }
      }
      const tab = event.target.closest && event.target.closest("[data-tab]");
      if (!tab) return;
      const next = tab.getAttribute("data-tab");
      if (!next || next === this._tab) return;
      this._tab = next;
      this._saveTab(next);
      this._render();
    }

    async _refreshViolations() {
      if (this._refreshingViolations || !this._hass || !this._config.violation_entity) return;
      this._refreshingViolations = true;
      this._render();
      try {
        try {
          await this._hass.callService("12123", "refresh_violations", {
            entity_id: this._config.violation_entity,
          });
        } catch (_) {
          await this._hass.callService("shaobo_12123", "refresh_violations", {
            entity_id: this._config.violation_entity,
          });
        }
      } catch (error) {
        console.error(`[${TAG}] 更新违章记录失败:`, error);
      } finally {
        this._refreshingViolations = false;
        this._signature = "";
        this._render();
      }
    }

    _empty(text) { return `<div class="empty"><ha-icon icon="mdi:check-circle-outline"></ha-icon><span>${this._text(text)}</span></div>`; }

    _tabStorageKey() {
      return `ha-12123-tab:${this._config?.status_entity || "default"}`;
    }

    _loadTab() {
      try {
        const value = window.localStorage.getItem(this._tabStorageKey());
        return ["overview", "vehicles", "violations", "messages"].includes(value) ? value : "overview";
      } catch (_error) {
        return "overview";
      }
    }

    _saveTab(tab) {
      try {
        window.localStorage.setItem(this._tabStorageKey(), tab);
      } catch (_error) {
        // Storage may be unavailable in private browsing; keep the current tab for this session.
      }
    }

    _messageStorageKey() {
      return `ha-12123-message-category:${this._config?.status_entity || "default"}`;
    }

    _loadMessageCategory() {
      try {
        const value = window.localStorage.getItem(this._messageStorageKey());
        return ["all", "business", "service"].includes(value) ? value : "all";
      } catch (_error) {
        return "all";
      }
    }

    _saveMessageCategory(category) {
      try {
        window.localStorage.setItem(this._messageStorageKey(), category);
      } catch (_error) {
        // Storage may be unavailable in private browsing; the card still works for this session.
      }
    }

    _asArray(value) {
      return Array.isArray(value) ? value : [];
    }

    _withUnit(value, unit) { return value === undefined || value === null || value === "" ? "" : `${value}${unit}`; }

    _formatDate(value) {
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return String(value);
      const pad = (part) => String(part).padStart(2, "0");
      return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
    }

    _text(value) {
      return String(value === undefined || value === null ? "-" : value)
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
        .replace(/\"/g, "&quot;").replace(/'/g, "&#39;");
    }

    _attr(value) {
      return this._text(value).replace(/`/g, "&#96;");
    }
  }

  if (!customElements.get(TAG)) customElements.define(TAG, Jiaoguan12123Card);
  window.customCards = window.customCards || [];
  if (!window.customCards.some((card) => card && card.type === TAG)) {
    window.customCards.push({
      type: TAG,
      name: "12123",
      description: "12123 用户、驾驶证、车辆、违章与消息面板",
      preview: false,
    });
  }
  console.info(`%c ${TAG} %c v${VERSION} `, "background:#1976d2;color:white;padding:2px 4px;font-weight:bold", "background:white;color:#1976d2;padding:2px 4px;font-weight:bold");
})();
