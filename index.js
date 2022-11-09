const fs = require("fs")
const path = require("path")
const {KalmanFilter} = require('kalman-filter');
const kf = new KalmanFilter();

let Dir = `./kmou_dataset003`
let Filename = `/kmou_dataset003`
let DownName = `/kmou_dataset003`
let SaveDir = `./kmou_dataset004`

let lenNum = 110

for(let i=lenNum; i<=lenNum; i++){
    new Promise((resolve, reject) => {
        setTimeout(() => {
            A(i);
        }, 1000);          
    })
    .then((data) => {
        console.log(data)
    });
}

async function A (num){
let FILE_NAME = `${Dir}${Filename}_${num}.csv`
let csvPath = path.join(__dirname,FILE_NAME);
let csv = fs.readFileSync(csvPath,"utf-8")
let rows = csv.split("\r\n")


if(rows[rows.length - 1] === ''){
    
    console.log("empty")
    rows.pop()
}

let results = []
let columnTitle = []
for (const i in rows){
    const row = rows[i]
    const data = row.split(",")
    if (i === "0"){
        columnTitle = data
    } else {
        let row_data = {}
        for (const index in columnTitle) {
            changeString = columnTitle[index].replace(/ /g, "_").replace(/-/g,"_").trim()
            const title = changeString.trim()
            if(index === "1" || index === "2"){
            row_data[title] = data[index]
            }else {
            row_data[title] = Number(data[index])
            }
        }
        results.push(row_data)
    }
}

let A_data = [];
let B_data = []; 
let C_data = []; 
let D_data = []; 
let E_data = []; 

for(let e in results ){
    A_data.push(results[e].Tachometer)
    B_data.push(results[e].Engine_body_vibration_at_fore_top_transverse_direction)
    C_data.push(results[e].Engine_body_vibration_at_fore_top_vertical_direction)
    D_data.push(results[e].Engine_body_vibration_at_aft_top_transverse_direction)
    E_data.push(results[e].Engine_body_vibration_at_aft_top_transverse_direction)
}
A_data = kf.filterAll(A_data)
B_data = kf.filterAll(B_data)
C_data = kf.filterAll(C_data)
D_data = kf.filterAll(D_data)
E_data = kf.filterAll(E_data)
    
for (let i in results){
    results[i].Tachometer = +A_data[i][0].toFixed(4)
    results[i].Engine_body_vibration_at_fore_top_longitudinal_direction = +B_data[i][0].toFixed(8)
    results[i].Engine_body_vibration_at_fore_top_transverse_direction = +C_data[i][0].toFixed(8)
    results[i].Engine_body_vibration_at_fore_top_vertical_direction = +D_data[i][0].toFixed(8)
    results[i].Engine_body_vibration_at_aft_top_transverse_direction = +E_data[i][0].toFixed(8)
}
await CSV(results,num)
console.log(`Kalman ${FILE_NAME} ... done`)
}


async function CSV (data,i){
    let title = Object.keys(data[0])
    let writeStream = fs.createWriteStream(`${SaveDir}${DownName}_${i}.csv`)
await (data.forEach((data, index) => {
    let newLine = []
    if(index === 0){
        newLine.push(title)
        writeStream.write(newLine.join(',')+ '\r\n', () => {
        })
    }else{
    for(let el in title){
    let tit = title[el]
    if(el === "2"){
        newLine.push(new Date().toISOString())
    } else {
    newLine.push(data[tit])
    }
}
    writeStream.write(newLine.join(',')+ '\r\n', () => {
    })
}
}))

writeStream.end()

writeStream.on('finish', () => {
    console.log('finish write stream, moving along')
}).on('error', (err) => {
    console.log(err)
})
}
