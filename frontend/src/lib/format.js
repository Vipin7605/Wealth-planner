
export const money=(n,compact=false)=>new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR',maximumFractionDigits:0,...(compact?{notation:'compact',maximumFractionDigits:1}:{})}).format(n||0);
export const COLORS=['#7ee2ad','#75a9ef','#b9a4f3','#efc983','#f49696','#63c9d8','#aec78c','#c6b5a0','#e7a9ca','#91a6bd'];
