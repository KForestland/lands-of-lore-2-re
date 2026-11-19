/* Native x87 reproduction of the recovered initializer's arithmetic.
   Host execution, not a DOSBox capture. Constants are supplied from the game. */
#include <stdint.h>
#include <stdio.h>
int main(int argc,char **argv) {
    if(argc!=2)return 2;
    FILE *f=fopen(argv[1],"rb"); if(!f)return 3;
    double constants[2]; if(fread(constants,8,2,f)!=2){fclose(f);return 4;} fclose(f);
    unsigned short oldcw,cw=0x037f;
    __asm__ volatile("fnstcw %0":"=m"(oldcw));
    __asm__ volatile("fldcw %0"::"m"(cw));
    for(int32_t i=0;i<4096;i++) {
        int32_t out;
        __asm__ volatile("fldl %1; fimull %2; fsin; fmull %3; fisttpl %0"
            :"=m"(out):"m"(constants[0]),"m"(i),"m"(constants[1]):"st");
        if(fwrite(&out,4,1,stdout)!=1)return 5;
    }
    __asm__ volatile("fldcw %0"::"m"(oldcw));
    return 0;
}
