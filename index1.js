const fs = require("fs")
const path = require("path")
const ObjectsToCsv = require('objects-to-csv');
const {KalmanFilter} = require('kalman-filter');
const kf = new KalmanFilter();
const createCsvWriter = require('csv-writer').createObjectCsvWriter;

let Dir = `./kmou_004`
let Filename = `/kmou_dataset004`
let DownName = `/kalman_dataset004`
let SaveDir = `./kmou_004_filter`

let lenNum = 261

for(let i=lenNum; i<=lenNum; i++){
    // new Promise((resolve, reject) => {
    //     setTimeout(() => {
    //         A(i);
    //     }, 1000);          
    // })
    // .then((data) => {
    // 	console.log("@@@@@@@@@@@@@@@@@@@@@@@@@@");
    // });
    (A(i))
}

// async function makeCSV (results) {
//     let Rcsv = new ObjectsToCsv(results);
    
//     // Save to file:
//     await Rcsv.toDisk(`./kalman_dataset009-4.csv`,{allColumns: true});
    
//     // Return the CSV file as string:
//     // console.log(await Rcsv.toString());
//     console.log("makeCSV 함수")
// }; _${num}
async function A (num){
let FILE_NAME = `${Dir}${Filename}_${num}.csv`
//let FILE_NAME = `${Dir}${Filename}-${num}.csv`
let csvPath = path.join(__dirname,FILE_NAME);
let csv = fs.readFileSync(csvPath,"utf-8")
let rows = csv.split("\r\n")
// 저장된 파일이 빈 csv파일일때, 아래것으로 실행

//let rows = csv.split("\n")

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
            //row_data[title] = 1
        }
        results.push(row_data)
    }
}
console.log(results)

// let A_data = [];
// for(let e in results ){
//     A_data.push(results[e].x)
// }
// let B_data = []; 
// for(let e in results ){
//     B_data.push(results[e].y)
// }
// let C_data = []; 
// for(let e in results ){
//     C_data.push(results[e].z)
// }

let A_data = [];
let B_data = []; 
let C_data = []; 
let D_data = []; 
let E_data = []; 

//         {id:title[3], title: "Tachometer"},
//         {id:title[4], title: "Engine_body_vibration_at_fore_top_longitudinal_direction"},
//         {id:title[5], title: "Engine_body_vibration_at_fore_top_transverse_direction"},
//         {id:title[6], title: "Engine_body_vibration_at_fore_top_vertical_direction"},
//         {id:title[7], title: "Engine_body_vibration_at_aft_top_transverse_direction"},

// for(let e in results ){
//     A_data.push(results[e].Tachometer)
//     B_data.push(results[e].Engine_body_vibration_at_fore_top_longitudinal_direction)
//     C_data.push(results[e].Engine_body_vibration_at_fore_top_transverse_direction)
//     D_data.push(results[e].Engine_body_vibration_at_fore_top_vertical_direction)
//     E_data.push(results[e].Engine_body_vibration_at_aft_top_transverse_direction)
// }
// for(let e in results ){
//     A_data.push(+results[e].DRAFT_AFT.toFixed(2))
//     B_data.push(+results[e].DRAFT_FWD.toFixed(2))
//     C_data.push(+results[e].DRAFT_PORT.toFixed(2))
//     D_data.push(+results[e].DRAFT_STBD.toFixed(2))
// }

// A_data = kf.filterAll(A_data)
// B_data = kf.filterAll(B_data)
// C_data = kf.filterAll(C_data)

// A_data = kf.filterAll(A_data)
// B_data = kf.filterAll(B_data)
// C_data = kf.filterAll(C_data)
// D_data = kf.filterAll(D_data)

// A_data = kf.filterAll(A_data)
// B_data = kf.filterAll(B_data)
// C_data = kf.filterAll(C_data)
// D_data = kf.filterAll(D_data)
// E_data = kf.filterAll(E_data)

// let recursion = 0
// results.map((e) =>{
    

// for (let i in results){
//     results[i].Tachometer = +A_data[i][0].toFixed(4)
//     results[i].Engine_body_vibration_at_fore_top_longitudinal_direction = +B_data[i][0].toFixed(8)
//     results[i].Engine_body_vibration_at_fore_top_transverse_direction = +C_data[i][0].toFixed(8)
//     results[i].Engine_body_vibration_at_fore_top_vertical_direction = +D_data[i][0].toFixed(8)
//     results[i].Engine_body_vibration_at_aft_top_transverse_direction = +E_data[i][0].toFixed(8)
// }
// for (let i in results){
//     results[i].DRAFT_AFT = A_data[i][0].toFixed(2)
//     results[i].DRAFT_FWD = B_data[i][0].toFixed(2)
//     results[i].DRAFT_PORT = C_data[i][0].toFixed(2)
//     results[i].DRAFT_STBD = D_data[i][0].toFixed(2)
// }

// for (let i in results){
//     results[i].x = A_data[i][0]
//     results[i].y = B_data[i][0]
//     results[i].z = C_data[i][0]
// }
// console.log(results.slice(0,5))

await CSV(results,num)
// // await makeCSV(results)
console.log(`Kalman ${FILE_NAME} ... done`)
}


async function CSV (data,i){
    // console.log(Object.keys(data[0]))
    let title = Object.keys(data[0])
    // const csvWriter = createCsvWriter({
    //     path: `${SaveDir}${DownName}-${i}.csv`,
    //     header : [
    //         {id:title[0], title: "MMSI"},
    //         {id:title[1], title: "ShipName"},
    //         {id:title[2], title: "DataInfo"},
    //         {id:title[3], title: "Tachometer"},
    //         {id:title[4], title: "Engine_body_vibration_at_fore_top_longitudinal_direction"},
    //         {id:title[5], title: "Engine_body_vibration_at_fore_top_transverse_direction"},
    //         {id:title[6], title: "Engine_body_vibration_at_fore_top_vertical_direction"},
    //         {id:title[7], title: "Engine_body_vibration_at_aft_top_transverse_direction"},
    //         // {id:title[8], title: "Temperature"},
    //         // {id:title[9], title: "Humidity"}
    //     ]
    // })
    // await csvWriter.writeRecords(data)
    // .then(()=>{
    //     console.log("Save ... Done ")
    // })  _${i}
    let writeStream = fs.createWriteStream(`${SaveDir}${DownName}_${i}.csv`)
    console.log(title)
await (data.forEach((data, index) => {
    let newLine = []
    if(index === 0){
        newLine.push(title)
        writeStream.write(newLine.join(',')+ '\r\n', () => {
            // a line was written to stream
        })
    }else{
    for(let el in title){
    let tit = title[el]
    // console.log(data[tit])
    if(el === "2"){
        newLine.push(new Date().toISOString())
    } else{
    newLine.push(data[tit])
    }
}
    writeStream.write(newLine.join(',')+ '\r\n', () => {
        // a line was written to stream
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

// //

// function convertArrayOfObjectsToCSV(args) {  
//     var result, ctr, keys, columnDelimiter, lineDelimiter, data;

//     data = args.data || null;
//     if (data == null || !data.length) {
//         return null;
//     }

//     columnDelimiter = args.columnDelimiter || ',';
//     lineDelimiter = args.lineDelimiter || '\n';

//     keys = Object.keys(data[0]);

//     result = '';
//     result += keys.join(columnDelimiter);
//     result += lineDelimiter;

//     data.forEach(function(item) {
//         ctr = 0;
//         keys.forEach(function(key) {
//             if (ctr > 0) result += columnDelimiter;

//             result += item[key];
//             ctr++;
//         });
//         result += lineDelimiter;
//     });

//     return result;
// }
// function downloadCSV(args) {  
//     var data, filename, link;
//     var csv = convertArrayOfObjectsToCSV({
//         data: stockData
//     });
//     if (csv == null) return;

//     filename = args.filename || 'export.csv';

//     if (!csv.match(/^data:text\/csv/i)) {
//         csv = 'data:text/csv;charset=utf-8,' + csv;
//     }
//     data = encodeURI(csv);

// }