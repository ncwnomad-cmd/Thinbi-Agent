import express from "express";
const app = express();
app.use(express.json());
app.get("/", (_req,res)=>res.json({status:"ok",service:"thinbi-instagram-agent"}));
app.get("/health", (_req,res)=>res.json({ok:true}));
app.get("/webhook",(req,res)=>{
  if(req.query["hub.mode"]==="subscribe" && req.query["hub.verify_token"]===process.env.META_VERIFY_TOKEN)
    return res.status(200).send(req.query["hub.challenge"]);
  res.sendStatus(403);
});
app.post("/webhook",(_req,res)=>res.sendStatus(200));
const port=process.env.PORT||3000;
app.listen(port,()=>console.log(`Listening on ${port}`));
