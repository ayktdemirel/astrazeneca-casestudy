import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { tap, catchError } from 'rxjs/operators';

const API_URL = '/api';

export interface Competitor {
    id: string;
    name: string;
    headquarters?: string;
    therapeuticAreas?: string[];
    activeDrugs?: number;
    pipelineDrugs?: number;
    createdAt?: string;
}

export interface ClinicalTrial {
    id: string;
    competitorId: string;
    trialId: string;
    drugName: string;
    phase?: string;
    indication?: string;
    status?: string;
    startDate?: string;
    estimatedCompletion?: string;
    enrollmentTarget?: number;
}

@Injectable({
    providedIn: 'root'
})
export class CompetitorService {
    constructor(private http: HttpClient) { }

    getCompetitors(): Observable<Competitor[]> {
        return this.http.get<Competitor[]>(`${API_URL}/competitors`).pipe(
            tap(data => console.log('CompetitorService: Received data', data)),
            catchError(err => {
                console.error('CompetitorService: Error', err);
                throw err;
            })
        );
    }

    createCompetitor(competitor: Competitor): Observable<Competitor> {
        return this.http.post<Competitor>(`${API_URL}/competitors`, competitor).pipe(
            tap(data => console.log('CompetitorService: Created', data))
        );
    }

    updateCompetitor(id: string, competitor: Competitor): Observable<Competitor> {
        return this.http.put<Competitor>(`${API_URL}/competitors/${id}`, competitor).pipe(
            tap(data => console.log('CompetitorService: Updated', data))
        );
    }

    deleteCompetitor(id: string): Observable<void> {
        return this.http.delete<void>(`${API_URL}/competitors/${id}`).pipe(
            tap(() => console.log('CompetitorService: Deleted', id))
        );
    }

    getTrials(competitorId: string): Observable<ClinicalTrial[]> {
        return this.http.get<ClinicalTrial[]>(`${API_URL}/competitors/${competitorId}/trials`);
    }
}
