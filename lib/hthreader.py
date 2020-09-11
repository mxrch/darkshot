# -*- coding: utf-8 -*- 

import threading
from time import sleep
from collections import deque
import traceback
import requests

"""Outil de parallélisation de processus répétitif"""
class Threader:
    def __init__(self,max_threads):
        """
        Args:
            max_threads: nombre de threads à utiliser.
        """
        self.n=max_threads

        self.resources=[None for i in range(max_threads)]
        self.kill=False

        self.feedqueue=deque([])
        self.feedlock = threading.Lock()

        self.resultqueue=deque([])
        self.resultlock = threading.Lock()

        self.masterthread = threading.Thread(target=self.masterthread)

        self.threads = [threading.Thread(target=self.slavethread, args=(i,)) for i in range(max_threads)]
        for th in self.threads:
            th.daemon = True
            th.start()
        self.masterthread.daemon=True
        self.masterthread.start()
    
    def feed(self,f,args,label=None):
        """
        Args:
            f: fonction à traiter
            args: tuple d'arguments à donner à la fonction
        """
        self.feedList(f,(args,),label)

    def feedList(self,f,argslist,label=None):
        """
        Args:
            f: fonction à traiter
            argslist: liste des tuples d'arguments à donner à la fonction
        """
        self.feedlock.acquire()
        for args in argslist:
            self.feedqueue.appendleft((f,args,label))
        self.feedlock.release()

    def getEmptyThreadId(self):
        """
        Returns:
            int: L'ID d'un thread disponible, -1 si aucun ne l'est
        """
        for i in range(self.n):
            if self.resources[i]==None:return i
        return -1

    def areThreadsEmpty(self):
        """
        Returns:
            bool: True si aucun thread n'est en cours de travail, False sinon
        """
        for i in range(self.n):
            if self.resources[i]!=None:
                return False
        return True

    def isIdle(self):
        """
        Returns:
            bool: True si aucun travail n'est en cours, False sinon
        """
        if not len(self.feedqueue)==0:return False
        if not self.areThreadsEmpty():return False
        #if not len(self.resultqueue)==0:return False

        return True

    def masterthread(self):
        """
            Thread unique, assignant leurs tâches aux slavethreads
        """
        while not self.kill:
            idle=True
            empty = self.getEmptyThreadId()
            self.feedlock.acquire()
            if len(self.feedqueue)>0 and empty>=0:
                idle=False
                self.resources[empty]=self.feedqueue.pop()
            self.feedlock.release()
            if idle:
                sleep(0.001)

    def slavethread(self, i):
        """
            Thread assurant l'execution d'une tache donnée par le masterthread
        """
        while not self.kill:
            while self.resources[i]==None:
                sleep(0.001)
                if self.kill:return
            
            response = None
            try:
                response = self.resources[i][0](**self.resources[i][1])
            except requests.exceptions.ReadTimeout as err:
                print("Timeout on "+self.resources[i][2])
                response = {"timeout":"timeout"}
            except Exception as ex:
                print(traceback.format_exc())
                response = {"error":"error"}
            if response!=None:
                self.resultlock.acquire()
                self.resultqueue.appendleft((response,self.resources[i],self.resources[i][2]))
                self.resultlock.release()

            self.resources[i]=None

    def getresult(self):
        result=[]
        if len(self.resultqueue)>0:
            self.resultlock.acquire()
            result = self.resultqueue
            self.resultqueue = deque()
            self.resultlock.release()
        return result
    
    def getresultDict(self):
        """
        Recovers all return values from executed functions as a dict, using the identification strings given in "feed" as keys
        """
        result={}
        if len(self.resultqueue)>0:
            self.resultlock.acquire()
            res = self.resultqueue
            self.resultqueue = deque()
            self.resultlock.release()
            for e in res:
                result[e[2]] = e[0]
        return result

    def join(self):
        """
            Termine tous les threads (bloquant)
        """
        self.kill=True
        for th in self.threads:
            th.join()
        self.masterthread.join()

    def finishJobs(self):
        while not self.isIdle():
            sleep(0.001)
        self.join()

