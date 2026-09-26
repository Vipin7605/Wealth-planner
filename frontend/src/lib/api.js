
export async function api(path,options={}){
 const res=await fetch('/api'+path,{credentials:'same-origin',...options,headers:{'Content-Type':'application/json',...options.headers}});
 if(!res.ok){let message='Request failed';try{const d=await res.json();message=typeof d.detail==='string'?d.detail:Array.isArray(d.detail)?d.detail.map(x=>`${x.loc.at(-1)}: ${x.msg}`).join('; '):message;}catch{message=await res.text().catch(()=>message);}throw Error(message);}
 return res.json();
}
export const post=(path,body={})=>api(path,{method:'POST',body:JSON.stringify(body)});
