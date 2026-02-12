import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { tap, catchError } from 'rxjs/operators';

const API_URL = '/api'; // Proxied by Nginx to Insights Service

export interface Insight {
    id: string;
    competitorId: string;
    title: string;
    description?: string;
    content: string;
    category?: string;
    therapeuticArea: string;
    impactLevel?: string;
    relevanceScore: number;
    source?: string;
    sourceDocumentId: string;
    publishedDate?: string;
    createdAt: string;
}

@Injectable({
    providedIn: 'root'
})
export class InsightsService {
    constructor(private http: HttpClient) { }

    getInsights(filters?: any): Observable<Insight[]> {
        return this.http.get<Insight[]>(`${API_URL}/insights`, { params: filters }).pipe(
            tap(data => console.log('InsightsService: Received data', data)),
            catchError(err => {
                console.error('InsightsService: Error', err);
                throw err;
            })
        );
    }

    getInsight(id: string): Observable<Insight> {
        return this.http.get<Insight>(`${API_URL}/insights/${id}`);
    }

    createInsight(insight: Partial<Insight>): Observable<Insight> {
        return this.http.post<Insight>(`${API_URL}/insights`, insight);
    }

    updateInsight(id: string, insight: Partial<Insight>): Observable<Insight> {
        return this.http.put<Insight>(`${API_URL}/insights/${id}`, insight);
    }

    deleteInsight(id: string): Observable<void> {
        return this.http.delete<void>(`${API_URL}/insights/${id}`);
    }
}
