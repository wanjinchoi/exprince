function make(){
    
    for(let i = 2; i<10; i++){
        let result = "";
        for(let j = 1; j<10; j++){
            result += ` ${i} * ${j} = ${i*j} `
        }
        console.log(result)   
    }
}
make()