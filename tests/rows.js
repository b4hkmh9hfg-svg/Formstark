const FSD=require("../daten.js");let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{process.stdout.write(JSON.stringify(FSD.sZuZeilen(JSON.parse(s))))});
