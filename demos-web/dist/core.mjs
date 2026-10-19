// Funciones puras compartidas por la aplicación y sus pruebas.
export function* csvRows(text, delimiter=',') {
  text = text.replace(/^\uFEFF/, '');
  let row=[], field='', quoted=false, closed=false;
  for(let i=0;i<text.length;i++) {
    const c=text[i];
    if(quoted) { if(c==='"') { if(text[i+1]==='"'){field+='"';i++;}else{quoted=false;closed=true;} } else field+=c; }
    else if(c==='"') { if(field.length||closed) throw Error('Comillas CSV inválidas.'); quoted=true; }
    else if(c===delimiter) {row.push(field);field='';closed=false;}
    else if(c==='\r'||c==='\n') {if(c==='\r'&&text[i+1]==='\n')i++;row.push(field);if(row.some(x=>x.trim()))yield row;row=[];field='';closed=false;}
    else {if(closed&&c.trim())throw Error('Texto después de comillas de cierre.');if(!closed)field+=c;}
  }
  if(quoted)throw Error('El CSV termina con comillas abiertas.');
  if(field.length||row.length){row.push(field);if(row.some(x=>x.trim()))yield row;}
}
const finite = value => typeof value==='string' && value.trim()!=='' && Number.isFinite(Number(value));
const inc=(m,k)=>m.set(k,(m.get(k)||0)+1);
const top=(m,n=6)=>[...m].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0])).slice(0,n);
export function mobility(text) {
  const rows=csvRows(text), first=rows.next();if(first.done)throw Error('El CSV está vacío.');
  const headers=first.value.map(x=>x.trim()), start=headers.indexOf('Start Time'),duration=headers.indexOf('Trip Duration'),type=headers.indexOf('User Type'),station=headers.indexOf('Start Station');
  if(start<0||duration<0)throw Error('Faltan las columnas Start Time y Trip Duration.');
  if(new Set(headers).size!==headers.length)throw Error('Hay encabezados duplicados.');
  let count=0, rejected=0, sum=0;const hours=Array(24).fill(0),days=Array(7).fill(0),types=new Map(),stations=new Map();
  for(const row of rows){
    const m=(row[start]||'').trim().match(/^(\d{4}-\d{2}-\d{2})[ T](\d{2}):(\d{2}):(\d{2})(?:\.\d+)?$/),d=Number(row[duration]);
    const date=m?new Date(`${m[1]}T${m[2]}:${m[3]}:${m[4]}Z`):null;
    if(!m||!finite(row[duration])||d<0||!date||!Number.isFinite(date.getTime())||date.toISOString().slice(0,19)!==`${m[1]}T${m[2]}:${m[3]}:${m[4]}`){rejected++;continue;}
    count++;sum+=d;hours[+m[2]]++;days[(date.getUTCDay()+6)%7]++;
    inc(types,type<0?'Sin especificar':(row[type]||'Sin especificar'));
    inc(stations,station<0?'Sin especificar':(row[station]||'Sin especificar'));
  }
  if(!count)throw Error('No hay viajes válidos. Revisa fechas ISO y duración en segundos.');
  return {valid:count,rejected,averageSeconds:sum/count,hours,days,types:top(types),stations:top(stations),uniqueStations:stations.size};
}
export function spectra(text) {
  const firstLines=text.split(/\r?\n/).slice(0,10).join('\n');const delimiter=firstLines.includes(';')?';':',';
  const points=[];let discarded=0;
  for(const row of csvRows(text,delimiter)){
    if(row.length<2||!finite(row[0])||!finite(row[1])){discarded++;continue;}
    points.push([Number(row[0]),Number(row[1])]);
    if(points.length>200000)throw Error('Máximo 200 mil pares por espectro. Divide el archivo.');
  }
  if(points.length<2)throw Error('Se necesitan al menos dos pares numéricos en las primeras dos columnas.');
  points.sort((a,b)=>a[0]-b[0]);let peak=points[0],lo=points[0][1],hi=lo;
  for(const p of points){if(p[1]>peak[1])peak=p;lo=Math.min(lo,p[1]);hi=Math.max(hi,p[1]);}
  return {count:points.length,discarded,xMin:points[0][0],xMax:points.at(-1)[0],yMin:lo,yMax:hi,peak,points};
}
export function stix(bundles) {
  const types=new Map(),ids=new Set(),patterns=new Set(),kinds=new Map();let indicators=0,missingId=0,missingPattern=0,total=0;
  for(const bundle of bundles){
    if(!bundle||!Array.isArray(bundle.objects))throw Error('Cada archivo debe contener un bundle con una lista objects.');
    for(const obj of bundle.objects){
      if(!obj||typeof obj!=='object'||Array.isArray(obj))throw Error('Se encontró un objeto STIX inválido.');
      total++;inc(types,typeof obj.type==='string'?obj.type:'Sin tipo');if(obj.type!=='indicator')continue;
      indicators++;if(typeof obj.id==='string'&&obj.id)ids.add(obj.id);else missingId++;
      if(typeof obj.pattern==='string'&&obj.pattern.trim()){
        patterns.add(obj.pattern);const m=obj.pattern.match(/\[\s*([a-z][a-z0-9-]*)\s*:/i);inc(kinds,m?m[1]:'Otro patrón');
      }else missingPattern++;
    }
  }
  return {total,indicators,uniqueIds:ids.size,uniquePatterns:patterns.size,missingId,missingPattern,repeatedPatterns:indicators-missingPattern-patterns.size,types:top(types,20),kinds:top(kinds,12)};
}
export function quote(v) {
  const fields=['grams','hours','priceKg','watts','kwh','hourly','extra','percent','tax'];
  for(const field of fields)if(typeof v[field]!=='number'||!Number.isFinite(v[field])||v[field]<0)throw Error('Usa números finitos mayores o iguales a cero.');
  if(!['markup','margin'].includes(v.mode))throw Error('Elige recargo o margen.');
  if(v.grams<=0||v.hours<=0)throw Error('El peso y el tiempo deben ser mayores que cero.');
  if(v.mode==='margin'&&v.percent>=100)throw Error('El margen debe ser menor al 100 %.');
  if(v.percent>1000||v.tax>100)throw Error('El porcentaje supera el rango permitido.');
  const material=v.grams/1000*v.priceKg,kwhUsed=v.watts/1000*v.hours,electricity=kwhUsed*v.kwh,operation=v.hours*v.hourly;
  const base=material+electricity+operation+v.extra;
  const subtotal=v.mode==='margin'?base/(1-v.percent/100):base*(1+v.percent/100);
  const tax=subtotal*v.tax/100,profit=subtotal-base;
  if(!Number.isFinite(subtotal+tax))throw Error('Los valores generan un resultado fuera de rango.');
  return {material,electricity,operation,extra:v.extra,kwhUsed,base,profit,subtotal,tax,total:subtotal+tax,actualMargin:subtotal?profit/subtotal*100:0};
}
export function bikeDemo(){let text='Start Time,Trip Duration,Start Station,User Type\n';for(let i=0;i<240;i++){const day=1+i%14,h=6+(i*7)%17; text+=`2025-09-${String(day).padStart(2,'0')} ${String(h).padStart(2,'0')}:15:00,${240+(i*137)%2400},Estación ${'ABCDE'[i%5]},${i%4?'Suscripción':'Ocasional'}\n`;}return text;}
export function spectrumDemo(){let t='File,Espectro sintético\nX,Amplitud arbitraria\n';for(let i=0;i<301;i++){const x=1540+i/10,y=0.2+3*Math.exp(-(((x-1552)/1.4)**2))+1.3*Math.exp(-(((x-1560)/2)**2))+0.025*Math.sin(i*2.1);t+=`${x.toFixed(2)},${y.toFixed(6)}\n`;}return t;}
export function stixDemo(){return {type:'bundle',objects:[{type:'indicator',id:'indicator--demo-1',pattern:"[domain-name:value = 'example.invalid']"},{type:'indicator',id:'indicator--demo-2',pattern:"[domain-name:value = 'example.invalid']"},{type:'indicator',id:'indicator--demo-3',pattern:"[ipv4-addr:value = '192.0.2.1']"},{type:'indicator',id:'indicator--demo-4',pattern:"[file:hashes.'SHA-256' = 'DEMO']"},{type:'indicator',id:'indicator--demo-5'},{type:'malware',name:'Objeto sintético'},{type:'relationship',relationship_type:'indicates'},{type:'relationship',relationship_type:'indicates'}]};}
