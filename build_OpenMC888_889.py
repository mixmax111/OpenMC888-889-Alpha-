import re

js_code = r"""
javascript:(function(){
    $('#mczte-main-modal, #mczte-celllock-modal, #mczte-band-modal, #mczte-dns-modal, #mczte-info-modal, #mczte-align-modal, #mczte-stats-modal').remove();
    if(window._mczteInterval) clearInterval(window._mczteInterval);

    /* =====================================================
       PARTE 1 — ALIGN WIZARD (Assistente Puntamento)
       Adattato da OpenMF258A01.js per API goform mczte/889
    ===================================================== */
    window.AlignWizard = {
        timer: null,
        mode: 'menu',
        step: 0,
        measurements: {},
        currentMeasureTicks: 0,
        tempData: { rsrp: [], sinr: [], pci: [], cell: [] },
        bestCardinal: '',

        /* Legge RSRP, SINR, PCI, CellID via goform GET (non OAM) */
        doGetRequest: function(callback) {
            try {
                $.ajax({
                    type: 'GET', timeout: 3000,
                    url: '/goform/goform_get_cmd_process',
                    data: { cmd: 'lte_rsrp,lte_snr,lte_pci,cell_id', multi_data: '1' },
                    dataType: 'json',
                    success: function(data) {
                        var rsrp = parseInt(data.lte_rsrp, 10);
                        var sinr = parseInt(data.lte_snr, 10);
                        var pci  = data.lte_pci  ? parseInt(data.lte_pci, 16).toString()  : 'N/D';
                        var cell = data.cell_id  ? parseInt(data.cell_id, 16).toString()  : 'N/D';
                        if(isNaN(rsrp)) rsrp = -140;
                        if(isNaN(sinr)) sinr  = -20;
                        if(callback) callback(rsrp, sinr, pci, cell);
                    }
                });
            } catch(e) {}
        },

        modeMostFrequent: function(arr) {
            if(arr.length === 0) return 'N/D';
            var counts = {}, maxCount = 0, maxEl = arr[0];
            for(var i=0; i<arr.length; i++) {
                var el = arr[i];
                counts[el] = (counts[el] || 0) + 1;
                if(counts[el] > maxCount) { maxCount = counts[el]; maxEl = el; }
            }
            return maxEl;
        },

        startMeasurement: function(positionName, durationSeconds, nextStepFunction) {
            var self = this;
            self.tempData = { rsrp: [], sinr: [], pci: [], cell: [] };
            self.currentMeasureTicks = 0;
            var maxTicks = durationSeconds;
            $('#aw-progress-container').show();
            $('#aw-menu').hide();
            $('#aw-btn-next').hide();
            $('#aw-btn-cancel').show();
            self.timer = setInterval(function() {
                self.doGetRequest(function(rsrp, sinr, pci, cell) {
                    if(rsrp > -140) {
                        self.tempData.rsrp.push(rsrp);
                        self.tempData.sinr.push(sinr);
                        if(pci  !== 'N/D') self.tempData.pci.push(pci);
                        if(cell !== 'N/D') self.tempData.cell.push(cell);
                    }
                    var pct = Math.round((self.currentMeasureTicks / maxTicks) * 100);
                    $('#aw-progress-bar').css('width', pct + '%');
                    $('#aw-live-stats').text('RSRP: ' + rsrp + ' dBm | SINR: ' + sinr + ' dB | PCI: ' + pci);
                });
                self.currentMeasureTicks++;
                if(self.currentMeasureTicks >= maxTicks) {
                    clearInterval(self.timer); self.timer = null;
                    var avgRsrp = -140, avgSinr = -20;
                    if(self.tempData.rsrp.length > 0) {
                        var sumR = 0, sumS = 0;
                        for(var i=0; i<self.tempData.rsrp.length; i++) { sumR += self.tempData.rsrp[i]; sumS += self.tempData.sinr[i]; }
                        avgRsrp = Math.round(sumR / self.tempData.rsrp.length);
                        avgSinr = Math.round(sumS / self.tempData.sinr.length);
                    }
                    self.measurements[positionName] = { rsrp: avgRsrp, sinr: avgSinr, pci: self.modeMostFrequent(self.tempData.pci), cell: self.modeMostFrequent(self.tempData.cell) };
                    $('#aw-progress-container').hide();
                    $('#aw-btn-next').show();
                    $('#aw-btn-cancel').hide();
                    nextStepFunction();
                }
            }, 1000);
        },

        getScore: function(meas) { return !meas ? -999 : meas.rsrp + (meas.sinr * 2); },

        formatMeas: function(meas) {
            if(!meas) return '<span style="color:#94a3b8">nessun dato</span>';
            var pciStr = (meas.pci && meas.pci !== 'N/D') ? ' <span style="color:#94a3b8;font-size:12px">[PCI: <span style="color:#10b981">' + meas.pci + '</span>]</span>' : '';
            return 'RSRP: <b>' + meas.rsrp + '</b> dBm | SINR: <b>' + meas.sinr + '</b> dB' + pciStr;
        },

        updateUI: function(title, desc, btnText, btnAction) {
            $('#aw-menu').hide();
            $('#aw-title').text(title);
            $('#aw-desc').html(desc);
            if(btnText && btnAction) { $('#aw-btn-next').show().text(btnText).off('click').on('click', btnAction); }
            else { $('#aw-btn-next').hide(); }
        },

        showMenu: function() {
            var self = this;
            self.mode = 'menu';
            if(self.timer) { clearInterval(self.timer); self.timer = null; }
            $('#aw-title').text('📡 Assistente Puntamento');
            $('#aw-desc').html('Scegli la fase di allineamento.<br><span style="color:#94a3b8;font-size:12px">Il sistema traccia il PCI (torre) agganciato durante le misurazioni.</span>');
            $('#aw-btn-next').hide(); $('#aw-btn-cancel').hide(); $('#aw-progress-container').hide(); $('#aw-live-stats').text('');
            $('#aw-menu').show();
            $('#aw-btn-macro').off('click').on('click',  function(){ self.mode='macro';  self.step=0; self.measurements={}; self.runMacro(); });
            $('#aw-btn-height').off('click').on('click', function(){ self.mode='height'; self.step=0; self.measurements={}; self.runHeight(); });
            $('#aw-btn-tilt').off('click').on('click',   function(){ self.mode='tilt';   self.step=0; self.measurements={}; self.runTilt(); });
            $('#aw-btn-fine').off('click').on('click',   function(){ self.mode='fine';   self.step=0; self.measurements={}; self.runFine(); });
        },

        runMacro: function() {
            var self = this;
            var dirs = [
                { key: 'Nord',  label: 'NORD',  next: 1 },
                { key: 'Est',   label: 'EST',   next: 2 },
                { key: 'Sud',   label: 'SUD',   next: 3 },
                { key: 'Ovest', label: 'OVEST', next: 4 }
            ];
            var d = dirs[self.step];
            if(d) {
                var prevKey = self.step > 0 ? dirs[self.step-1].key : null;
                var prevInfo = prevKey ? '<br><br>📊 ' + dirs[self.step-1].label + ': ' + self.formatMeas(self.measurements[prevKey]) : '';
                self.updateUI('Macro ' + (self.step+1) + '/8: Punta a ' + d.label,
                    'Usa la bussola del telefono. Punta l\'antenna a <b>' + d.label + '</b>.' + prevInfo,
                    '▶ AVVIA (30s)',
                    function(){ self.startMeasurement(d.key, 30, function(){ self.step=d.next; self.runMacro(); }); });
            } else if(self.step === 4) {
                var pts = ['Nord','Est','Sud','Ovest'];
                var best = pts[0], maxScore = self.getScore(self.measurements[best]);
                for(var i=1; i<4; i++) { var s=self.getScore(self.measurements[pts[i]]); if(s>maxScore){maxScore=s; best=pts[i];} }
                self.bestCardinal = best;
                var rows = '';
                for(var j=0; j<4; j++) {
                    var isWin = pts[j]===best;
                    rows += '<div style="padding:6px 0;border-bottom:1px solid #1e293b;' + (isWin?'color:#fcd34d':'') + '">' + (isWin?'🏆 ':'') + '<b>' + pts[j] + '</b>: ' + self.formatMeas(self.measurements[pts[j]]) + '</div>';
                }
                self.updateUI('Macro 5/8: Risultato Quadranti',
                    rows + '<br>Riporta l\'antenna a <b>' + best.toUpperCase() + '</b> per il test ±45°.',
                    'HO PUNTATO A ' + best.toUpperCase() + ' →',
                    function(){ self.step=5; self.runMacro(); });
            } else if(self.step === 5) {
                self.updateUI('Macro 6/8: -45° (Sinistra)',
                    'Da <b>' + self.bestCardinal + '</b>, ruota l\'antenna a <b>SINISTRA di 45°</b>.',
                    '▶ AVVIA (30s)',
                    function(){ self.startMeasurement('Best_Left45', 30, function(){ self.step=6; self.runMacro(); }); });
            } else if(self.step === 6) {
                self.updateUI('Macro 7/8: +45° (Destra)',
                    '📊 -45°: ' + self.formatMeas(self.measurements['Best_Left45']) + '<br><br>Riporta l\'antenna a <b>' + self.bestCardinal + '</b> e ruota a <b>DESTRA di 45°</b>.',
                    '▶ AVVIA (30s)',
                    function(){ self.startMeasurement('Best_Right45', 30, function(){ self.step=7; self.runMacro(); }); });
            } else if(self.step === 7) {
                var c=self.measurements[self.bestCardinal], l=self.measurements['Best_Left45'], r=self.measurements['Best_Right45'];
                var bScore=self.getScore(c), lScore=self.getScore(l), rScore=self.getScore(r);
                var winner=self.bestCardinal;
                if(lScore>bScore){winner='-45° (Sinistra)'; bScore=lScore;}
                if(rScore>bScore){winner='+45° (Destra)';}
                var txt='<div style="padding:6px 0;border-bottom:1px solid #1e293b">Centro (' + self.bestCardinal + '): ' + self.formatMeas(c) + '</div>' +
                        '<div style="padding:6px 0;border-bottom:1px solid #1e293b">Sinistra (-45°): ' + self.formatMeas(l) + '</div>' +
                        '<div style="padding:6px 0">Destra (+45°): ' + self.formatMeas(r) + '</div>' +
                        '<br>🏆 <b style="color:#fcd34d">Settore migliore: ' + winner + '</b>';
                self.updateUI('Macro 8/8: Risultato Finale', txt, '← TORNA AL MENU', function(){ self.showMenu(); });
            }
        },

        runHeight: function() {
            var self = this;
            if(self.step===0) {
                self.updateUI('Altezza 1/3: Posizione Base','Misura la posizione attuale come riferimento.','▶ AVVIA (30s)',
                    function(){ self.startMeasurement('H_Base',30,function(){ self.step=1; self.runHeight(); }); });
            } else if(self.step===1) {
                self.updateUI('Altezza 2/3: Alza il palo','📊 Base: ' + self.formatMeas(self.measurements['H_Base']) + '<br><br><b>Alza il palo</b> di circa 20–30 cm.','▶ AVVIA (30s)',
                    function(){ self.startMeasurement('H_Su',30,function(){ self.step=2; self.runHeight(); }); });
            } else if(self.step===2) {
                self.updateUI('Altezza 3/3: Abbassa il palo','📊 In alto: ' + self.formatMeas(self.measurements['H_Su']) + '<br><br><b>Abbassa il palo</b> sotto il livello base.','▶ AVVIA (30s)',
                    function(){ self.startMeasurement('H_Giu',30,function(){ self.step=3; self.runHeight(); }); });
            } else if(self.step===3) {
                var b=self.measurements['H_Base'], u=self.measurements['H_Su'], d=self.measurements['H_Giu'];
                var bestName='Base', bestScore=self.getScore(b);
                if(self.getScore(u)>bestScore){bestName='In Alto'; bestScore=self.getScore(u);}
                if(self.getScore(d)>bestScore){bestName='In Basso';}
                var txt='<div style="padding:6px 0;border-bottom:1px solid #1e293b">In Alto: '+self.formatMeas(u)+'</div>'+
                        '<div style="padding:6px 0;border-bottom:1px solid #1e293b">Base: '+self.formatMeas(b)+'</div>'+
                        '<div style="padding:6px 0">In Basso: '+self.formatMeas(d)+'</div>'+
                        '<br>🏆 <b style="color:#fcd34d">Altezza consigliata: '+bestName+'</b>';
                self.updateUI('Risultato Altezza', txt,'← TORNA AL MENU',function(){ self.showMenu(); });
            }
        },

        runTilt: function() {
            var self = this;
            if(self.step===0) {
                self.updateUI('Tilt 1/3: Posizione Neutra','Metti l\'antenna perpendicolare al terreno.','▶ AVVIA (30s)',
                    function(){ self.startMeasurement('T_Base',30,function(){ self.step=1; self.runTilt(); }); });
            } else if(self.step===1) {
                self.updateUI('Tilt 2/3: Inclina verso l\'ALTO','📊 Neutro: '+self.formatMeas(self.measurements['T_Base'])+'<br><br>Inclina l\'antenna verso l\'<b>ALTO (+5°)</b>.','▶ AVVIA (30s)',
                    function(){ self.startMeasurement('T_Su',30,function(){ self.step=2; self.runTilt(); }); });
            } else if(self.step===2) {
                self.updateUI('Tilt 3/3: Inclina verso il BASSO','📊 Alto: '+self.formatMeas(self.measurements['T_Su'])+'<br><br>Inclina l\'antenna verso il <b>BASSO (-5°)</b>.','▶ AVVIA (30s)',
                    function(){ self.startMeasurement('T_Giu',30,function(){ self.step=3; self.runTilt(); }); });
            } else if(self.step===3) {
                var b=self.measurements['T_Base'], u=self.measurements['T_Su'], d=self.measurements['T_Giu'];
                var bestName='Neutro (dritto)', bestScore=self.getScore(b);
                if(self.getScore(u)>bestScore){bestName='Inclinato in ALTO'; bestScore=self.getScore(u);}
                if(self.getScore(d)>bestScore){bestName='Inclinato in BASSO';}
                var txt='<div style="padding:6px 0;border-bottom:1px solid #1e293b">Alto: '+self.formatMeas(u)+'</div>'+
                        '<div style="padding:6px 0;border-bottom:1px solid #1e293b">Neutro: '+self.formatMeas(b)+'</div>'+
                        '<div style="padding:6px 0">Basso: '+self.formatMeas(d)+'</div>'+
                        '<br>🏆 <b style="color:#fcd34d">Tilt consigliato: '+bestName+'</b>';
                self.updateUI('Risultato Tilt', txt,'← TORNA AL MENU',function(){ self.showMenu(); });
            }
        },

        runFine: function() {
            var self = this;
            if(self.step===0) {
                self.updateUI('Fine Tuning 1/3: Centro','Misura la posizione attuale.','▶ AVVIA (30s)',
                    function(){ self.startMeasurement('F_Centro',30,function(){ self.step=1; self.runFine(); }); });
            } else if(self.step===1) {
                self.updateUI('Fine Tuning 2/3: Micro-Sinistra','📊 Centro: '+self.formatMeas(self.measurements['F_Centro'])+'<br><br>Sposta l\'antenna a <b>SINISTRA di 5–10°</b>.','▶ AVVIA (30s)',
                    function(){ self.startMeasurement('F_Sin',30,function(){ self.step=2; self.runFine(); }); });
            } else if(self.step===2) {
                self.updateUI('Fine Tuning 3/3: Micro-Destra','📊 Sinistra: '+self.formatMeas(self.measurements['F_Sin'])+'<br><br>Sposta l\'antenna a <b>DESTRA di 5–10°</b> rispetto al centro.','▶ AVVIA (30s)',
                    function(){ self.startMeasurement('F_Des',30,function(){ self.step=3; self.runFine(); }); });
            } else if(self.step===3) {
                var c=self.measurements['F_Centro'], l=self.measurements['F_Sin'], r=self.measurements['F_Des'];
                var bestName='Centro', bestScore=self.getScore(c);
                if(self.getScore(l)>bestScore){bestName='Sinistra'; bestScore=self.getScore(l);}
                if(self.getScore(r)>bestScore){bestName='Destra';}
                var txt='<div style="padding:6px 0;border-bottom:1px solid #1e293b">Sinistra: '+self.formatMeas(l)+'</div>'+
                        '<div style="padding:6px 0;border-bottom:1px solid #1e293b">Centro: '+self.formatMeas(c)+'</div>'+
                        '<div style="padding:6px 0">Destra: '+self.formatMeas(r)+'</div>'+
                        '<br>🏆 <b style="color:#fcd34d">Posizione consigliata: '+bestName+'</b>';
                self.updateUI('Risultato Fine Tuning', txt,'← TORNA AL MENU',function(){ self.showMenu(); });
            }
        },

        initUI: function() {
            $('#mczte-align-modal').remove();
            if($('#AlignCSS888').length===0) {
                $('head').append('<style id="AlignCSS888">' +
                    '.aw8-modal{position:fixed;top:5%;left:50%;transform:translateX(-50%);width:95%;max-width:520px;max-height:90vh;overflow-y:auto;background:rgba(15,23,42,0.98);border:2px solid #38bdf8;border-radius:12px;z-index:10000001;box-shadow:0 25px 50px rgba(0,0,0,.85);font-family:"Segoe UI",sans-serif;color:#f8fafc;padding:22px;text-align:center}' +
                    '.aw8-btn{background:#38bdf8;color:#0f172a;border:none;padding:13px 18px;border-radius:8px;cursor:pointer;font-weight:bold;font-size:15px;margin-top:12px;width:100%;transition:.2s}' +
                    '.aw8-btn:hover{background:#7dd3fc}' +
                    '.aw8-menu-btn{background:#1e293b;color:#f8fafc;border:1px solid #334155;font-size:14px;text-transform:uppercase;letter-spacing:.8px;padding:14px}' +
                    '.aw8-menu-btn:hover{background:#334155;border-color:#38bdf8}' +
                    '.aw8-progress-bg{background:#1e293b;border-radius:8px;height:10px;width:100%;margin-top:18px;overflow:hidden;display:none;border:1px solid #334155}' +
                    '.aw8-progress-bar{background:#10b981;height:100%;width:0%;transition:width 1s linear}' +
                    '</style>');
            }
            $('body').append(
                '<div id="mczte-align-modal" class="aw8-modal">' +
                '<h2 id="aw-title" style="margin-top:0;color:#38bdf8;font-size:20px">📡 Assistente Puntamento</h2>' +
                '<p id="aw-desc" style="font-size:14px;line-height:1.65;margin:16px 0;text-align:left"></p>' +
                '<div id="aw-menu" style="display:none">' +
                    '<button id="aw-btn-macro"  class="aw8-btn aw8-menu-btn">🧭 1. Primo Puntamento (Quadranti)</button>' +
                    '<button id="aw-btn-height" class="aw8-btn aw8-menu-btn">↕️ 2. Ottimizza Altezza</button>' +
                    '<button id="aw-btn-tilt"   class="aw8-btn aw8-menu-btn">📐 3. Ottimizza Inclinazione (Tilt)</button>' +
                    '<button id="aw-btn-fine"   class="aw8-btn aw8-menu-btn">🎯 4. Fine-Tuning Micrometrico</button>' +
                '</div>' +
                '<div id="aw-progress-container" class="aw8-progress-bg"><div id="aw-progress-bar" class="aw8-progress-bar"></div></div>' +
                '<div id="aw-live-stats" style="margin-top:12px;font-weight:bold;color:#fcd34d;font-size:14px;min-height:20px"></div>' +
                '<button id="aw-btn-next" class="aw8-btn" style="display:none"></button>' +
                '<button id="aw-btn-cancel" class="aw8-btn" style="display:none;background:transparent;color:#ef4444;border:1px solid #ef4444;margin-top:10px" onclick="if(window.AlignWizard.timer)clearInterval(window.AlignWizard.timer);window.AlignWizard.timer=null;window.AlignWizard.showMenu()">⏹ Interrompi Misurazione</button>' +
                '<div style="margin-top:22px;border-top:1px solid #1e293b;padding-top:14px">' +
                    '<button style="background:transparent;color:#64748b;border:none;cursor:pointer;font-size:13px" onclick="if(window.AlignWizard.timer)clearInterval(window.AlignWizard.timer);$(\'#mczte-align-modal\').remove()">✖ Chiudi Assistente</button>' +
                '</div>' +
                '</div>'
            );
            this.showMenu();
        }
    };

    /* =====================================================
       PARTE 2 — OpenMc888 889 (Cruscotto Principale)
    ===================================================== */
    window.Openmczte = {
        interval: null,
        signal: {},
        GW: 500, GH: 30, GT: 3,
        history: { rsrp:[], rsrq:[], sinr:[], nr5rsrp:[], nr5sinr:[] },

        safeText: function(val, def) {
            return (val===null||val===undefined||val===''||val==='N/A'||val==='None') ? def : val;
        },

        /* Recupera token AD e chiama callback(ad) */
        getAD: function(callback) {
            $.ajax({
                type:'GET', url:'/goform/goform_get_cmd_process',
                data:{ cmd:'wa_inner_version,cr_version,RD', multi_data:'1' },
                dataType:'json',
                success: function(data) {
                    var ad = cookWithRequest(cookWithRequest(data.wa_inner_version + data.cr_version) + data.RD);
                    callback(ad);
                },
                error: function(){ alert('Errore: impossibile ottenere il token AD.'); }
            });
        },

        /* POST goform con token AD */
        postGoform: function(payload, successCb) {
            var self = this;
            self.getAD(function(ad) {
                payload.AD = ad;
                payload.isTest = 'false';
                $.ajax({
                    type:'POST', url:'/goform/goform_set_cmd_process',
                    data: payload,
                    success: successCb || function(){},
                    error: function(){ alert('Errore durante la comunicazione con il modem.'); }
                });
            });
        },

        injectCSS: function() {
            if($('#mczteStyle').length > 0) return;
            $('head').append('<style id="mczteStyle">' +
                '.m8-modal{position:fixed;top:2%;left:50%;transform:translateX(-50%);width:95%;max-width:920px;max-height:96vh;overflow-y:auto;background:rgba(15,23,42,0.97);border:1px solid #1e293b;border-radius:14px;z-index:9999998;box-shadow:0 25px 60px rgba(0,0,0,.9);font-family:"Segoe UI",sans-serif;color:#f8fafc;padding:22px;backdrop-filter:blur(12px)}' +
                '.m8-header{display:flex;justify-content:space-between;align-items:center;border-bottom:2px solid #1e293b;padding-bottom:13px;margin-bottom:18px}' +
                '.m8-header h2{margin:0;color:#38bdf8;font-size:21px;font-weight:700;letter-spacing:.3px}' +
                '.m8-close{background:#ef4444;color:#fff;border:none;border-radius:6px;padding:8px 16px;cursor:pointer;font-weight:700;font-size:13px;transition:.2s}' +
                '.m8-close:hover{background:#dc2626;transform:translateY(-1px)}' +
                '.m8-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:18px}' +
                '@media(max-width:600px){.m8-grid{grid-template-columns:repeat(2,1fr)}}' +
                '.m8-card{background:#0f172a;padding:12px;border-radius:10px;text-align:center;border:1px solid #1e293b}' +
                '.m8-card-title{font-size:10px;color:#64748b;text-transform:uppercase;font-weight:700;letter-spacing:.6px;margin-bottom:4px}' +
                '.m8-card span{display:block;font-size:19px;font-weight:700;color:#e0f2fe}' +
                '.m8-card-wide{grid-column:span 4}' +
                '@media(max-width:600px){.m8-card-wide{grid-column:span 2}}' +
                '.m8-graph{margin-top:5px}' +
                '.m8-ca-card{grid-column:span 4;background:#0f172a;border-color:#1e40af}' +
                '@media(max-width:600px){.m8-ca-card{grid-column:span 2}}' +
                '.m8-ca-active{border-color:#ef4444!important}' +
                '.m8-nr-section{display:none}' +
                '.m8-actions{display:flex;justify-content:center;gap:8px;flex-wrap:wrap;margin-top:4px}' +
                '.m8-btn{border:none;padding:10px 16px;border-radius:8px;font-size:13px;font-weight:700;cursor:pointer;transition:.2s;box-shadow:0 4px 8px rgba(0,0,0,.3);color:#fff}' +
                '.m8-btn:hover{filter:brightness(1.2);transform:translateY(-2px)}' +
                '.m8-btn-primary{background:#3b82f6}' +
                '.m8-btn-warn{background:#f59e0b}' +
                '.m8-btn-danger{background:#ef4444}' +
                '.m8-btn-green{background:#10b981}' +
                '.m8-btn-purple{background:#8b5cf6}' +
                '.m8-btn-teal{background:#0ea5e9}' +
                '.m8-sub-modal{position:fixed;top:8%;left:50%;transform:translateX(-50%);width:92%;max-width:520px;max-height:88vh;overflow-y:auto;background:rgba(15,23,42,0.99);border:2px solid #334155;border-radius:12px;z-index:10000000;box-shadow:0 20px 50px rgba(0,0,0,.9);font-family:"Segoe UI",sans-serif;color:#f8fafc;padding:22px}' +
                '.m8-input{width:100%;box-sizing:border-box;padding:11px 13px;border-radius:7px;background:#0f172a;color:#f8fafc;border:1px solid #334155;font-size:14px;margin-top:6px;outline:none}' +
                '.m8-input:focus{border-color:#38bdf8}' +
                '.m8-label{display:block;font-size:11px;color:#94a3b8;text-transform:uppercase;font-weight:700;letter-spacing:.7px;margin-top:14px}' +
                'a.m8-link{color:#38bdf8;text-decoration:none}a.m8-link:hover{text-decoration:underline}' +
                '.m8-footer{margin-top:18px;padding-top:12px;border-top:1px solid #0f172a;text-align:center}' +
                '</style>');
        },

        renderMain: function() {
            $('body').append(
                '<div id="mczte-main-modal" class="m8-modal">' +
                '<div class="m8-header"><h2>📡 OpenMc888 889</h2><button class="m8-close" onclick="Openmczte.close()">✖ CHIUDI</button></div>' +
                '<div class="m8-grid">' +
                    '<div class="m8-card"><div class="m8-card-title">RSRP</div><span id="m8_rsrp">-</span><div id="m8_brsrp" class="m8-graph"></div></div>' +
                    '<div class="m8-card"><div class="m8-card-title">RSRQ</div><span id="m8_rsrq">-</span><div id="m8_brsrq" class="m8-graph"></div></div>' +
                    '<div class="m8-card"><div class="m8-card-title">SINR</div><span id="m8_sinr">-</span><div id="m8_bsinr" class="m8-graph"></div></div>' +
                    '<div class="m8-card"><div class="m8-card-title">Rete / Banda</div><span id="m8_netband" style="font-size:15px">-</span></div>' +
                    '<div class="m8-card m8-nr-section" id="m8_nr_card1"><div class="m8-card-title">NR RSRP</div><span id="m8_nr5rsrp">-</span><div id="m8_bnr5rsrp" class="m8-graph"></div></div>' +
                    '<div class="m8-card m8-nr-section" id="m8_nr_card2"><div class="m8-card-title">NR SINR</div><span id="m8_nr5sinr">-</span><div id="m8_bnr5sinr" class="m8-graph"></div></div>' +
                    '<div class="m8-card m8-nr-section" id="m8_nr_card3"><div class="m8-card-title">NR Banda</div><span id="m8_nrband" style="font-size:15px">-</span></div>' +
                    '<div class="m8-card m8-nr-section" id="m8_nr_card4"><div class="m8-card-title">NR PCI / EARFCN</div><span id="m8_nrpci" style="font-size:13px">-</span></div>' +
                    '<div class="m8-card"><div class="m8-card-title">ENB ID</div><span><a id="m8_lteitaly" class="m8-link" href="#" target="_blank">-</a></span></div>' +
                    '<div class="m8-card"><div class="m8-card-title">Sector ID</div><span id="m8_cellid">-</span></div>' +
                    '<div class="m8-card"><div class="m8-card-title">PCI / EARFCN</div><span id="m8_pci_earfcn" style="font-size:13px">-</span></div>' +
                    '<div class="m8-card"><div class="m8-card-title">IP WAN</div><span id="m8_wanip" style="font-size:13px">-</span></div>' +
                    '<div class="m8-card"><div class="m8-card-title">Temp 4G</div><span id="m8_temp4g">-</span></div>' +
                    '<div class="m8-card"><div class="m8-card-title">Temp 5G</div><span id="m8_temp5g">-</span></div>' +
                    '<div class="m8-card"><div class="m8-card-title">Cell Lock</div><span id="m8_lock" style="font-size:12px;color:#94a3b8">nessuno</span></div>' +
                    '<div class="m8-card"><div class="m8-card-title">DNS</div><span id="m8_dns" style="font-size:11px;color:#94a3b8">-</span></div>' +
                    '<div class="m8-card m8-ca-card" id="m8_ca_card"><div class="m8-card-title">Carrier Aggregation</div><span id="m8_ca" style="font-size:14px;color:#fcd34d">In attesa...</span></div>' +
                '</div>' +
                '<div class="m8-actions">' +
                    '<button class="m8-btn m8-btn-warn"    onclick="window.AlignWizard.initUI()">🎯 PUNTAMENTO</button>' +
                    '<button class="m8-btn" style="background:#0284c7" onclick="Openmczte.openStatsModal()">📊 GRAFICI LIVE</button>' +
                    '<button class="m8-btn m8-btn-primary" onclick="Openmczte.openCellLock()">🔒 CELL LOCK</button>' +
                    '<button class="m8-btn m8-btn-green"   onclick="Openmczte.openBandSelect()">📶 BANDE</button>' +
                    '<button class="m8-btn m8-btn-purple"  onclick="Openmczte.openDnsModal()">🌐 DNS</button>' +
                    '<button class="m8-btn m8-btn-teal"    onclick="Openmczte.openInfoModal()">ℹ️ INFO FW</button>' +
                    '<button class="m8-btn m8-btn-danger"  onclick="Openmczte.reboot()">🔄 REBOOT</button>' +
                '</div>' +
                '<div class="m8-footer"><a href="https://github.com/mixmax111/Openmczte-889-Alpha-" target="_blank" style="color:#334155;font-size:11px;text-decoration:none;letter-spacing:.4px" onmouseover="this.style.color=\'#38bdf8\'" onmouseout="this.style.color=\'#334155\'">by mix_max111 — Openmczte v1.0 Alpha</a></div>' +
                '</div>'
            );
        },

        barGraph: function(key, val, min, max) {
            var self = this;
            var hist = self.history[key];
            var boxcar = Math.floor(self.GW / (self.GT + 1));
            if(val > max) val = max;
            if(val < min) val = min;
            hist.unshift(val);
            if(hist.length > boxcar) hist.pop();
            var svg = '<svg viewBox="0 0 ' + self.GW + ' ' + self.GH + '" width="' + self.GW + '" height="' + self.GH + '" style="width:100%;height:' + self.GH + 'px;border:1px solid #1e293b;border-radius:4px;margin-top:4px">';
            for(var x=0; x<hist.length; x++) {
                var pax = (self.GT+1)*(x+1);
                var pby = self.GH - (hist[x]-min)/(max-min)*self.GH;
                var pc  = (hist[x]-min)/(max-min)*100;
                var color = pc<50 ? '#facc15' : (pc<85 ? '#10b981' : '#fb923c');
                svg += '<line x1="'+pax+'" y1="'+self.GH+'" x2="'+pax+'" y2="'+pby+'" stroke="'+color+'" stroke-width="'+self.GT+'"/>';
            }
            svg += '</svg>';
            $('#m8_b'+key).html(svg);
        },

        fetchData: function() {
            var self = this;
            if(!document.getElementById('mczte-main-modal')) return;
            $.ajax({
                type:'GET', url:'/goform/goform_get_cmd_process',
                data:{
                    cmd:'lte_pci,lte_pci_lock,lte_earfcn_lock,wan_ipaddr,wan_apn,pm_sensor_mdm,pm_modem_5g,nr5g_pci,nr5g_action_channel,nr5g_action_band,Z5g_SINR,Z5g_rsrp,wan_active_band,wan_active_channel,wan_lte_ca,lte_multi_ca_scell_info,cell_id,dns_mode,prefer_dns_manual,standby_dns_manual,network_type,rmcc,rmnc,lte_rsrq,lte_rssi,lte_rsrp,lte_snr,lte_ca_pcell_band,lte_ca_pcell_bandwidth',
                    multi_data:'1'
                },
                dataType:'json',
                success: function(d){ self.signal=d; self.updateUI(d); }
            });
        },

        updateUI: function(d) {
            var self = this;
            var rsrp = parseInt(d.lte_rsrp,10)||0, rsrq=parseInt(d.lte_rsrq,10)||0, sinr=parseInt(d.lte_snr,10)||0;
            $('#m8_rsrp').text(rsrp+' dBm'); $('#m8_rsrq').text(rsrq+' dB'); $('#m8_sinr').text(sinr+' dB');
            self.barGraph('rsrp',rsrp,-130,-60); self.barGraph('rsrq',rsrq,-16,-3); self.barGraph('sinr',sinr,0,24);
            var hasNR = d.nr5g_action_band && d.nr5g_action_band !== '';
            $('.m8-nr-section').toggle(hasNR);
            if(hasNR) {
                var nr5rsrp=parseInt(d.Z5g_rsrp,10)||0, nr5sinr=parseInt(d.Z5g_SINR,10)||0;
                $('#m8_nr5rsrp').text(nr5rsrp+' dBm'); $('#m8_nr5sinr').text(nr5sinr+' dB');
                $('#m8_nrband').text(d.nr5g_action_band);
                $('#m8_nrpci').text(parseInt(d.nr5g_pci,16)+' / '+d.nr5g_action_channel);
                self.barGraph('nr5rsrp',nr5rsrp,-130,-60); self.barGraph('nr5sinr',nr5sinr,0,24);
            }
            var bandMain = '';
            if(d.lte_ca_pcell_band && d.lte_ca_pcell_band!=='0') {
                bandMain = 'B'+d.lte_ca_pcell_band+(d.lte_ca_pcell_bandwidth?' @'+d.lte_ca_pcell_bandwidth+'MHz':'');
            } else if(d.wan_active_band) { bandMain=d.wan_active_band; }
            $('#m8_netband').text((d.network_type||'')+(bandMain?' · '+bandMain:''));
            var pciDec = d.lte_pci ? parseInt(d.lte_pci,16) : '-';
            $('#m8_pci_earfcn').text(pciDec+' / '+(d.wan_active_channel||'-'));
            var cellHex=parseInt(d.cell_id,16), enbId=isNaN(cellHex)?'-':Math.trunc(cellHex/256);
            var plmn=(d.rmcc||'')+(d.rmnc||'');
            if(plmn==='22201') plmn='2221';
            if(plmn==='22299') plmn='22288';
            if(plmn==='22250' && enbId.toString().length===6) plmn='22288';
            $('#m8_lteitaly').text(enbId!=='-'?enbId:'N/D').attr('href',enbId!=='-'?'https://lteitaly.it/internal/map.php#bts='+plmn+'.'+enbId:'#');
            $('#m8_cellid').text(isNaN(cellHex)?'-':cellHex);
            $('#m8_wanip').text(self.safeText(d.wan_ipaddr,'-'));
            $('#m8_temp4g').text(self.safeText(d.pm_sensor_mdm,'-')+(d.pm_sensor_mdm?'°':''));
            $('#m8_temp5g').text(self.safeText(d.pm_modem_5g,'-')+(d.pm_modem_5g?'°':''));
            if(d.lte_pci_lock && d.lte_pci_lock!=='0' && d.lte_pci_lock!=='') {
                $('#m8_lock').text('PCI '+d.lte_pci_lock+' / '+(d.lte_earfcn_lock||'-')).css('color','#ef4444');
            } else { $('#m8_lock').text('nessuno').css('color','#94a3b8'); }
            var dnsText='-';
            if(d.dns_mode==='manual') dnsText=(d.prefer_dns_manual||'?')+', '+(d.standby_dns_manual||'?');
            else if(d.dns_mode) dnsText=d.dns_mode.toUpperCase();
            $('#m8_dns').text(dnsText);
            var caActive = d.wan_lte_ca==='ca_activated';
            $('#m8_ca_card').toggleClass('m8-ca-active',caActive);
            var caHtml='';
            if(d.lte_multi_ca_scell_info && d.lte_multi_ca_scell_info!=='') {
                if(d.lte_ca_pcell_band && d.lte_ca_pcell_band!=='0') {
                    caHtml='<span style="display:inline-block;margin:3px 6px;padding:3px 8px;background:#1e293b;border-radius:5px;font-size:13px;color:#38bdf8">PCell B'+d.lte_ca_pcell_band+(d.lte_ca_pcell_bandwidth?' @'+d.lte_ca_pcell_bandwidth+'MHz':'')+'</span>';
                }
                var scells=d.lte_multi_ca_scell_info.slice(0,-1).split(';');
                for(var i=0;i<scells.length;i++) {
                    var parts=scells[i].split(',');
                    if(parts.length>=6) caHtml+='<span style="display:inline-block;margin:3px 6px;padding:3px 8px;background:#1e293b;border-radius:5px;font-size:13px;color:#fcd34d">B'+parts[3]+' @'+parts[5]+'MHz</span>';
                }
            }
            if(hasNR && d.nr5g_action_band) caHtml+='<span style="display:inline-block;margin:3px 6px;padding:4px 10px;background:#172554;border-radius:5px;font-size:14px;font-weight:bold;color:#93c5fd">'+d.nr5g_action_band+'</span>';
            if(!caHtml) caHtml='<span style="color:#475569">Nessuna banda aggregata</span>';
            $('#m8_ca').html(caHtml);
            if($('#mczte-stats-modal').length > 0) {
                self.updateStatsModal();
            }
        },

        startLoop: function() {
            var self=this;
            self.fetchData();
            self.interval=setInterval(function(){ self.fetchData(); },1500);
            window._mczteInterval=self.interval;
        },

        openCellLock: function() {
            $('#mczte-celllock-modal').remove();
            var d=this.signal;
            var curPci=d.lte_pci?parseInt(d.lte_pci,16):'', curEarfcn=d.wan_active_channel||'';
            $('body').append(
                '<div id="mczte-celllock-modal" class="m8-sub-modal">' +
                '<div class="m8-header"><h2>🔒 Cell Lock</h2><button class="m8-close" onclick="$(\'#mczte-celllock-modal\').remove()">✖</button></div>' +
                '<p style="color:#94a3b8;font-size:13px;margin-top:0">Blocca il modem su una cella specifica.<br><b style="color:#ef4444">Attenzione:</b> per rimuovere il lock è necessario fare il RESET del router.</p>' +
                '<label class="m8-label">PCI (Physical Cell ID)</label><input id="m8_input_pci" class="m8-input" type="number" placeholder="es. 116" value="'+curPci+'">' +
                '<label class="m8-label">EARFCN (frequenza)</label><input id="m8_input_earfcn" class="m8-input" type="number" placeholder="es. 3350" value="'+curEarfcn+'">' +
                '<div style="display:flex;gap:10px;margin-top:18px"><button class="m8-btn m8-btn-primary" style="flex:1" onclick="Openmczte.doCellLock()">🔒 APPLICA LOCK</button><button class="m8-btn" style="flex:1;background:#334155" onclick="$(\'#mczte-celllock-modal\').remove()">ANNULLA</button></div>' +
                '</div>'
            );
        },

        doCellLock: function() {
            var pci=$('#m8_input_pci').val().trim(), earfcn=$('#m8_input_earfcn').val().trim();
            if(!pci||!earfcn){ alert('Inserisci PCI e EARFCN.'); return; }
            if(!confirm('⚠️ Stai per bloccare il modem su PCI '+pci+' / EARFCN '+earfcn+'.\nPer rimuovere il lock sarà necessario il RESET del router. Continuare?')) return;
            this.postGoform({ goformId:'LTE_LOCK_CELL_SET', lte_pci_lock:pci, lte_earfcn_lock:earfcn }, function(res) {
                try { var j=JSON.parse(res); if(j.result==='success'){ alert('✅ Cell lock applicato!'); $('#mczte-celllock-modal').remove(); } else { alert('❌ Comando rifiutato dal modem.'); } }
                catch(e){ alert('Risposta inattesa dal modem.'); }
            });
        },

        openBandSelect: function() {
            $('#mczte-band-modal').remove();
            $('body').append(
                '<div id="mczte-band-modal" class="m8-sub-modal">' +
                '<div class="m8-header"><h2>📶 Selezione Bande</h2><button class="m8-close" onclick="$(\'#mczte-band-modal\').remove()">✖</button></div>' +
                '<div style="background:#0f172a;border-radius:8px;padding:14px;margin-bottom:16px">' +
                    '<h3 style="margin:0 0 8px;color:#38bdf8;font-size:15px">📶 Bande LTE (4G)</h3>' +
                    '<p style="color:#94a3b8;font-size:12px;margin:0 0 6px">Numeri banda separati da <b>+</b>, oppure <b>AUTO</b>. Es: <code style="color:#fcd34d">1+3+20</code></p>' +
                    '<input id="m8_lte_bands" class="m8-input" type="text" placeholder="AUTO" value="AUTO">' +
                    '<button class="m8-btn m8-btn-green" style="width:100%;margin-top:10px" onclick="Openmczte.doLteBands()">✅ APPLICA BANDE LTE</button>' +
                '</div>' +
                '<div style="background:#0f172a;border-radius:8px;padding:14px">' +
                    '<h3 style="margin:0 0 8px;color:#818cf8;font-size:15px">📡 Bande 5G NR</h3>' +
                    '<p style="color:#94a3b8;font-size:12px;margin:0 0 6px">Numeri banda NR separati da <b>+</b>, oppure <b>AUTO</b>. Es: <code style="color:#fcd34d">78</code></p>' +
                    '<input id="m8_nr_bands" class="m8-input" type="text" placeholder="AUTO" value="AUTO">' +
                    '<button class="m8-btn m8-btn-purple" style="width:100%;margin-top:10px" onclick="Openmczte.doNrBands()">✅ APPLICA BANDE 5G</button>' +
                '</div>' +
                '</div>'
            );
        },

        doLteBands: function() {
            var input=$('#m8_lte_bands').val().trim();
            if(!input) return;
            var mask;
            if(input.toUpperCase()==='AUTO') { mask='0xA3E2AB0908DF'; }
            else {
                var bs=input.split('+'), sum=0;
                for(var i=0;i<bs.length;i++){var n=parseInt(bs[i],10);if(!isNaN(n))sum+=Math.pow(2,n-1);}
                mask='0x'+sum.toString(16);
            }
            if(!confirm('Applicare le bande LTE: '+input+' ?')) return;
            this.postGoform({ goformId:'BAND_SELECT', is_gw_band:0, gw_band_mask:0, is_lte_band:1, lte_band_mask:mask }, function(){
                alert('✅ Bande LTE aggiornate!'); $('#mczte-band-modal').remove();
            });
        },

        doNrBands: function() {
            var input=$('#m8_nr_bands').val().trim();
            if(!input) return;
            var NR_ALL='1,2,3,5,7,8,20,28,38,41,50,51,66,70,71,74,75,76,77,78,79,80,81,82,83,84';
            var mask=input.toUpperCase()==='AUTO'?NR_ALL:input.split('+').join(',');
            if(!confirm('Applicare le bande 5G NR: '+input+' ?')) return;
            this.postGoform({ goformId:'WAN_PERFORM_NR5G_BAND_LOCK', nr5g_band_mask:mask }, function(){
                alert('✅ Bande 5G NR aggiornate!'); $('#mczte-band-modal').remove();
            });
        },

        openDnsModal: function() {
            $('#mczte-dns-modal').remove();
            var d=this.signal;
            var dns1=d.prefer_dns_manual||'', dns2=d.standby_dns_manual||'';
            $('body').append(
                '<div id="mczte-dns-modal" class="m8-sub-modal">' +
                '<div class="m8-header"><h2>🌐 Configurazione DNS</h2><button class="m8-close" onclick="$(\'#mczte-dns-modal\').remove()">✖</button></div>' +
                '<p style="color:#94a3b8;font-size:13px;margin-top:0">Imposta DNS personalizzati o ripristina quelli del provider.<br><span style="color:#64748b;font-size:11px">Cloudflare: 1.1.1.1 / 1.0.0.1 — Google: 8.8.8.8 / 8.8.4.4</span></p>' +
                '<label class="m8-label">DNS Primario</label><input id="m8_dns1" class="m8-input" type="text" placeholder="es. 1.1.1.1" value="'+dns1+'">' +
                '<label class="m8-label">DNS Secondario</label><input id="m8_dns2" class="m8-input" type="text" placeholder="es. 1.0.0.1" value="'+dns2+'">' +
                '<div style="display:flex;gap:10px;margin-top:14px">' +
                    '<button class="m8-btn m8-btn-primary" style="flex:1" onclick="Openmczte.doSetDns()">💾 SALVA DNS</button>' +
                    '<button class="m8-btn m8-btn-danger" style="flex:1" onclick="Openmczte.doAutoDns()">🔄 AUTO (Provider)</button>' +
                '</div>' +
                '</div>'
            );
        },

        doSetDns: function() {
            var self=this, dns1=$('#m8_dns1').val().trim(), dns2=$('#m8_dns2').val().trim();
            var apn=(self.signal&&self.signal.wan_apn)?self.signal.wan_apn:'';
            if(!dns1){ alert('Inserisci almeno il DNS primario.'); return; }
            if(!dns2) dns2=dns1;
            self.getAD(function(ad1){
                $.ajax({ type:'POST', url:'/goform/goform_set_cmd_process',
                    data:{ isTest:'false', goformId:'APN_PROC_EX', wan_apn:apn, profile_name:'Openmczte', apn_action:'save', apn_mode:'manual', pdp_type:'IP', dns_mode:'manual', prefer_dns_manual:dns1, standby_dns_manual:dns2, index:1, AD:ad1 },
                    success: function(){
                        self.getAD(function(ad2){
                            $.ajax({ type:'POST', url:'/goform/goform_set_cmd_process',
                                data:{ isTest:'false', goformId:'APN_PROC_EX', apn_mode:'manual', apn_action:'set_default', set_default_flag:1, pdp_type:'IP', pdp_type_roaming:'IP', index:1, AD:ad2 },
                                success: function(){ alert('✅ DNS impostati: '+dns1+' / '+dns2); $('#mczte-dns-modal').remove(); },
                                error: function(){ alert('Errore nella seconda chiamata DNS.'); }
                            });
                        });
                    },
                    error: function(){ alert('Errore nel salvataggio DNS.'); }
                });
            });
        },

        doAutoDns: function() {
            var self=this;
            if(!confirm('Ripristinare i DNS automatici del provider?')) return;
            var apn=(self.signal&&self.signal.wan_apn)?self.signal.wan_apn:'';
            self.getAD(function(ad){
                $.ajax({ type:'POST', url:'/goform/goform_set_cmd_process',
                    data:{ isTest:'false', goformId:'APN_PROC_EX', wan_apn:apn, profile_name:'Openmczte', apn_action:'save', apn_mode:'manual', pdp_type:'IP', dns_mode:'auto', prefer_dns_manual:'', standby_dns_manual:'', index:1, AD:ad },
                    success: function(){ alert('✅ DNS ripristinati (AUTO).'); $('#mczte-dns-modal').remove(); },
                    error: function(){ alert('Errore nel ripristino DNS.'); }
                });
            });
        },

        openInfoModal: function() {
            $('#mczte-info-modal').remove();
            $.ajax({
                type:'GET', url:'/goform/goform_get_cmd_process',
                data:{ cmd:'hardware_version,web_version,wa_inner_version,cr_version', multi_data:'1' },
                dataType:'json',
                success: function(d){
                    $('body').append(
                        '<div id="mczte-info-modal" class="m8-sub-modal">' +
                        '<div class="m8-header"><h2>ℹ️ Informazioni Firmware</h2><button class="m8-close" onclick="$(\'#mczte-info-modal\').remove()">✖</button></div>' +
                        '<table style="width:100%;border-collapse:collapse;font-size:14px">' +
                            '<tr style="border-bottom:1px solid #1e293b"><td style="padding:10px;color:#64748b">Hardware</td><td style="padding:10px;font-weight:bold">'+(d.hardware_version||'-')+'</td></tr>' +
                            '<tr style="border-bottom:1px solid #1e293b"><td style="padding:10px;color:#64748b">Web</td><td style="padding:10px;font-weight:bold">'+(d.web_version||'-')+'</td></tr>' +
                            '<tr style="border-bottom:1px solid #1e293b"><td style="padding:10px;color:#64748b">WA Inner</td><td style="padding:10px;font-weight:bold">'+(d.wa_inner_version||'-')+'</td></tr>' +
                            '<tr><td style="padding:10px;color:#64748b">CR</td><td style="padding:10px;font-weight:bold">'+(d.cr_version||'-')+'</td></tr>' +
                        '</table>' +
                        '<button class="m8-btn m8-btn-primary" style="width:100%;margin-top:16px" onclick="$(\'#mczte-info-modal\').remove()">CHIUDI</button>' +
                        '</div>'
                    );
                },
                error: function(){ alert('Impossibile leggere le versioni dal modem.'); }
            });
        },

        reboot: function() {
            if(!confirm('⚠️ Sei sicuro di voler riavviare il modem?\nLa connessione sarà interrotta per circa 1-2 minuti.')) return;
            this.postGoform({ goformId:'REBOOT_DEVICE' }, function(){
                alert('🔄 Riavvio in corso...'); Openmczte.close();
            });
        },

        drawDetailChart: function(targetId, key, minScale, maxScale, title, unit, color) {
            var hist = this.history[key];
            if(!hist || hist.length === 0) return;
            var cur = hist[0];
            var minV = hist[0], maxV = hist[0], sum = 0;
            for(var i=0; i<hist.length; i++) {
                if(hist[i] < minV) minV = hist[i];
                if(hist[i] > maxV) maxV = hist[i];
                sum += hist[i];
            }
            var avgV = (sum / hist.length).toFixed(1);
            var W = 550, H = 85;
            var points = [];
            var n = hist.length;
            for(var x = 0; x < n; x++) {
                var px = W - (x / (n > 1 ? n - 1 : 1)) * W;
                var clamped = Math.max(minScale, Math.min(maxScale, hist[x]));
                var py = H - ((clamped - minScale) / (maxScale - minScale)) * (H - 12) - 6;
                points.push(px.toFixed(1) + "," + py.toFixed(1));
            }
            var polylinePoints = points.join(" ");
            var areaPath = "M " + W + "," + H + " L " + polylinePoints + " L 0," + H + " Z";

            var html = '<div style="background:#0f172a;border:1px solid #1e293b;border-radius:8px;padding:10px;margin-bottom:10px">' +
                '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;flex-wrap:wrap;gap:4px">' +
                    '<span style="font-weight:700;color:#f8fafc;font-size:13px">' + title + '</span>' +
                    '<div style="font-size:11px;color:#94a3b8">' +
                        'Attuale: <b style="color:' + color + ';font-size:13px">' + cur + ' ' + unit + '</b> | ' +
                        'Min: <b style="color:#e2e8f0">' + minV + '</b> | ' +
                        'Max: <b style="color:#e2e8f0">' + maxV + '</b> | ' +
                        'Media: <b style="color:#38bdf8">' + avgV + '</b>' +
                    '</div>' +
                '</div>' +
                '<svg viewBox="0 0 ' + W + ' ' + H + '" style="width:100%;height:85px;background:#090d16;border-radius:6px;border:1px solid #1e293b">' +
                    '<line x1="0" y1="20" x2="' + W + '" y2="20" stroke="#1e293b" stroke-dasharray="4"/>' +
                    '<line x1="0" y1="42" x2="' + W + '" y2="42" stroke="#1e293b" stroke-dasharray="4"/>' +
                    '<line x1="0" y1="65" x2="' + W + '" y2="65" stroke="#1e293b" stroke-dasharray="4"/>' +
                    '<path d="' + areaPath + '" fill="' + color + '" fill-opacity="0.18"/>' +
                    '<polyline points="' + polylinePoints + '" fill="none" stroke="' + color + '" stroke-width="2"/>' +
                '</svg>' +
            '</div>';

            $('#' + targetId).html(html);
        },

        openStatsModal: function() {
            $('#mczte-stats-modal').remove();
            $('body').append(
                '<div id="mczte-stats-modal" class="m8-sub-modal" style="max-width:760px;width:95%">' +
                '<div class="m8-header"><h2>📊 Statistiche & Grafici Live</h2><button class="m8-close" onclick="$(\'#mczte-stats-modal\').remove()">✖</button></div>' +
                '<p style="color:#94a3b8;font-size:12px;margin-top:0;margin-bottom:12px">Monitoraggio grafico e metriche min/max/media in tempo reale (aggiornato ogni 1.5s). Traccia le ultime ~120 misurazioni.</p>' +
                '<div id="m8_stats_container"></div>' +
                '<button class="m8-btn m8-btn-primary" style="width:100%;margin-top:6px" onclick="$(\'#mczte-stats-modal\').remove()">CHIUDI</button>' +
                '</div>'
            );
            this.updateStatsModal();
        },

        updateStatsModal: function() {
            if($('#mczte-stats-modal').length === 0) return;
            if($('#st_rsrp').length === 0) {
                var html = '<div id="st_rsrp"></div><div id="st_sinr"></div><div id="st_rsrq"></div>';
                var hasNR = this.signal && this.signal.nr5g_action_band && this.signal.nr5g_action_band !== '';
                if(hasNR) {
                    html += '<div id="st_nr5rsrp"></div><div id="st_nr5sinr"></div>';
                }
                $('#m8_stats_container').html(html);
            }
            this.drawDetailChart('st_rsrp', 'rsrp', -130, -60, '📶 LTE RSRP (Potenza Segnale 4G)', 'dBm', '#38bdf8');
            this.drawDetailChart('st_sinr', 'sinr', 0, 30, '⚡ LTE SINR (Qualità / Disturbo 4G)', 'dB', '#10b981');
            this.drawDetailChart('st_rsrq', 'rsrq', -20, -3, '📊 LTE RSRQ (Qualità Segnale 4G)', 'dB', '#f59e0b');

            var hasNR = this.signal && this.signal.nr5g_action_band && this.signal.nr5g_action_band !== '';
            if(hasNR) {
                this.drawDetailChart('st_nr5rsrp', 'nr5rsrp', -130, -60, '🚀 5G NR RSRP (Potenza Segnale 5G)', 'dBm', '#818cf8');
                this.drawDetailChart('st_nr5sinr', 'nr5sinr', 0, 30, '⚡ 5G NR SINR (Qualità / Disturbo 5G)', 'dB', '#c084fc');
            }
        },

        close: function() {
            clearInterval(this.interval);
            if(window.AlignWizard && window.AlignWizard.timer) clearInterval(window.AlignWizard.timer);
            $('#mczte-main-modal, #mczte-celllock-modal, #mczte-band-modal, #mczte-dns-modal, #mczte-info-modal, #mczte-align-modal, #mczte-stats-modal').remove();
        },

        init: function() {
            this.injectCSS();
            this.renderMain();
            this.startLoop();
        }
    };

    window.Openmczte.init();
})();
"""

minified = re.sub(r'^\s+', '', js_code, flags=re.MULTILINE)
minified = minified.replace('\n', '')

print(minified)
