import { Component, OnInit, NgZone, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { forkJoin } from 'rxjs';
import { catchError, of } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { InsightsService, Insight } from '../../core/services/insights.service';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { InsightDetailDialogComponent } from '../insights/insight-detail-dialog';

interface DashboardStat {
  label: string;
  value: string;
  icon: string;
  color: string;
  bg: string;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatDialogModule
  ],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss'
})
export class DashboardComponent implements OnInit {
  stats: DashboardStat[] = [
    { label: 'Total Competitors', value: '—', icon: 'business', color: 'text-blue-600', bg: 'bg-blue-100' },
    { label: 'Active Insights', value: '—', icon: 'lightbulb', color: 'text-yellow-600', bg: 'bg-yellow-100' },
    { label: 'Documents Ingested', value: '—', icon: 'article', color: 'text-purple-600', bg: 'bg-purple-100' },
    { label: 'Notifications', value: '—', icon: 'notifications', color: 'text-green-600', bg: 'bg-green-100' }
  ];

  recentInsights: Insight[] = [];
  loading = true;

  constructor(
    private http: HttpClient,
    private insightsService: InsightsService,
    private router: Router,
    private dialog: MatDialog,
    private zone: NgZone,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit() {
    this.loading = true;
    forkJoin({
      competitors: this.http.get<any[]>('/api/competitors').pipe(catchError(() => of([]))),
      insights: this.insightsService.getInsights().pipe(catchError(() => of([]))),
      documents: this.http.get<any[]>('/api/crawl/documents').pipe(catchError(() => of([]))),
      notifications: this.http.get<any[]>('/api/notifications/me').pipe(catchError(() => of([])))
    }).subscribe(({ competitors, insights, documents, notifications }) => {
      this.zone.run(() => {
        this.stats = [
          { label: 'Total Competitors', value: String(competitors.length), icon: 'business', color: 'text-blue-600', bg: 'bg-blue-100' },
          { label: 'Active Insights', value: String(insights.length), icon: 'lightbulb', color: 'text-yellow-600', bg: 'bg-yellow-100' },
          { label: 'Documents Ingested', value: String(documents.length), icon: 'article', color: 'text-purple-600', bg: 'bg-purple-100' },
          { label: 'Notifications', value: String(notifications.length), icon: 'notifications', color: 'text-green-600', bg: 'bg-green-100' }
        ];

        this.recentInsights = insights
          .sort((a: Insight, b: Insight) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
          .slice(0, 5);

        this.loading = false;
        this.cdr.detectChanges();
      });
    });
  }

  getImpactColor(insight: Insight): string {
    const score = insight.relevanceScore || 0;
    if (score >= 8) return 'bg-red-100 text-red-700';
    if (score >= 5) return 'bg-yellow-100 text-yellow-700';
    return 'bg-blue-100 text-blue-700';
  }

  getImpactLabel(insight: Insight): string {
    const score = insight.relevanceScore || 0;
    if (score >= 8) return 'High Priority';
    if (score >= 5) return 'Medium Priority';
    return 'Low Priority';
  }

  openInsight(insight: Insight) {
    this.dialog.open(InsightDetailDialogComponent, {
      data: insight,
      width: '600px',
      maxWidth: '90vw',
      maxHeight: '85vh',
      autoFocus: false,
      position: { top: '80px' }
    });
  }

  navigateTo(path: string) {
    this.router.navigate([path]);
  }
}
