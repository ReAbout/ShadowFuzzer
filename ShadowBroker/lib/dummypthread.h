#ifndef DUMMYPTHREAD_H
#define DUMMYPTHREAD_H

#ifdef WITH_FUZZER
#else
#define pthread_create(A, B, C, D)
#endif

#define pthread_join(A, B)
#define pthread_cancel(A)

#define pthread_mutex_init(A, B)
#define pthread_mutex_destroy(A)
#define pthread_mutex_lock(A) 
#define pthread_mutex_unlock(A) 

#endif
