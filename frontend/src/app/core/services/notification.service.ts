import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { tap } from 'rxjs/operators';

const API_URL = '/api'; // Proxied by Nginx to Notification Service

export interface NotificationHistory {
    id: string;
    userId: string;
    insightId?: string;
    channel: string;
    message?: string;
    payload?: any;
    status: string;
    sentAt: string;
    read: boolean;
}

export interface Subscription {
    id?: string;
    userId?: string;
    therapeuticAreas: string[];
    competitorIds: string[];
    channels: string[];
    createdAt?: string;
}

@Injectable({
    providedIn: 'root'
})
export class NotificationService {
    private unreadCountSubject = new BehaviorSubject<number>(0);
    unreadCount$ = this.unreadCountSubject.asObservable();

    constructor(private http: HttpClient) { }

    createSubscription(subscription: Subscription): Observable<Subscription> {
        let headers = {};
        if (subscription.userId) {
            headers = { 'X-User-Id': subscription.userId };
        }
        return this.http.post<Subscription>(`${API_URL}/subscriptions`, subscription, { headers });
    }

    getSubscriptions(): Observable<Subscription[]> {
        return this.http.get<Subscription[]>(`${API_URL}/subscriptions`);
    }

    getMyNotifications(): Observable<NotificationHistory[]> {
        return this.http.get<NotificationHistory[]>(`${API_URL}/notifications/me`).pipe(
            tap(notifications => {
                const unread = notifications.filter(n => !n.read).length;
                this.unreadCountSubject.next(unread);
            })
        );
    }

    updateUnreadCount(): void {
        this.getMyNotifications().subscribe();
    }
}
