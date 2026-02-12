import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

const API_URL = '/api'; // Proxied by Nginx to Crawler Service

export interface CrawlJob {
    id: string;
    source: string;
    query: string;
    schedule: string;
    enabled: boolean;
}

export interface Document {
    id: string;
    source: string;
    title: string;
    url: string;
    processed: boolean;
    ingestedAt: string;
}

@Injectable({
    providedIn: 'root'
})
export class CrawlerService {
    constructor(private http: HttpClient) { }

    getJobs(): Observable<CrawlJob[]> {
        // Mock for now as endpoint might not exist or be different
        return this.http.get<CrawlJob[]>(`${API_URL}/crawl/jobs`);
    }

    createJob(job: Partial<CrawlJob>): Observable<CrawlJob> {
        return this.http.post<CrawlJob>(`${API_URL}/crawl/jobs`, job);
    }

    triggerRun(jobId: string): Observable<any> {
        return this.http.post(`${API_URL}/crawl/run`, null, { params: { job_id: jobId } });
    }

    deleteJob(jobId: string): Observable<void> {
        return this.http.delete<void>(`${API_URL}/crawl/jobs/${jobId}`);
    }

    updateJob(jobId: string, job: Partial<CrawlJob>): Observable<CrawlJob> {
        return this.http.put<CrawlJob>(`${API_URL}/crawl/jobs/${jobId}`, job);
    }

    getDocuments(): Observable<Document[]> {
        return this.http.get<Document[]>(`${API_URL}/crawl/documents`);
    }
}
