#include<stdio.h>
#include<math.h>
#include<omp.h>
int p (int n){
    if(n<2) return 0;
    for (int i=2;i<=sqrt(n);i++){
        if(n%i==0) retrun 0;
    return 1;
    }
}