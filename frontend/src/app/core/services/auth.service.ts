import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { map, tap } from 'rxjs/operators';
import { Router } from '@angular/router';

// Environment variable or hardcoded for now (Docker service name logic might need proxy)
const API_URL = '/api'; // Proxied by Nginx to User Management Service

export interface User {
    id: string;
    email: string;
    role: string;
    is_active: boolean;
}

export interface AuthResponse {
    accessToken: string;
    tokenType: string;
}

@Injectable({
    providedIn: 'root'
})
export class AuthService {
    private currentUserSubject: BehaviorSubject<User | null>;
    public currentUser: Observable<User | null>;

    constructor(private http: HttpClient, private router: Router) {
        const savedUser = localStorage.getItem('currentUser');
        this.currentUserSubject = new BehaviorSubject<User | null>(savedUser ? JSON.parse(savedUser) : null);
        this.currentUser = this.currentUserSubject.asObservable();
    }

    public get currentUserValue(): User | null {
        return this.currentUserSubject.value;
    }

    login(username: string, password: string): Observable<AuthResponse> {
        return this.http.post<AuthResponse>(`${API_URL}/auth/login`, { email: username, password })
            .pipe(map(response => {
                // Build a dummy user object from token or fetch /me
                // For now, let's fetch /me after login
                localStorage.setItem('token', response.accessToken);
                return response;
            }));
    }

    fetchMe(): Observable<User> {
        return this.http.get<User>(`${API_URL}/users/me`).pipe(
            tap(user => {
                localStorage.setItem('currentUser', JSON.stringify(user));
                this.currentUserSubject.next(user);
            })
        );
    }

    register(email: string, password: string): Observable<User> {
        return this.http.post<User>(`${API_URL}/users`, { email, password });
    }

    logout() {
        localStorage.removeItem('currentUser');
        localStorage.removeItem('token');
        this.currentUserSubject.next(null);
        this.router.navigate(['/auth/login']);
    }

    getToken(): string | null {
        return localStorage.getItem('token');
    }

    get isAdmin(): boolean {
        const user = this.currentUserValue;
        return user?.role === 'ADMIN';
    }

    get isAnalyst(): boolean {
        const user = this.currentUserValue;
        return user?.role === 'ANALYST';
    }

    get isExecutive(): boolean {
        const user = this.currentUserValue;
        return user?.role === 'EXECUTIVE';
    }

    hasRole(roles: string[]): boolean {
        const user = this.currentUserValue;
        return user ? roles.includes(user.role) : false;
    }
}
