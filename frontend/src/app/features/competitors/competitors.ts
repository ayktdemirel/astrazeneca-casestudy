import { Component, OnInit, NgZone, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { trigger, state, style, transition, animate } from '@angular/animations';
import { CompetitorService, Competitor, ClinicalTrial } from '../../core/services/competitor.service';
import { AuthService } from '../../core/services/auth.service';
import { CompetitorDialogComponent } from './competitor-dialog/competitor-dialog';

@Component({
    selector: 'app-competitors',
    standalone: true,
    imports: [
        CommonModule,
        MatCardModule,
        MatTableModule,
        MatIconModule,
        MatButtonModule,
        MatChipsModule,
        MatDialogModule,
        MatTooltipModule,
        MatSnackBarModule,
        MatProgressSpinnerModule
    ],
    templateUrl: './competitors.html',
    styleUrl: './competitors.scss',
    animations: [
        trigger('detailExpand', [
            state('collapsed,void', style({ height: '0px', minHeight: '0' })),
            state('expanded', style({ height: '*' })),
            transition('expanded <=> collapsed', animate('225ms cubic-bezier(0.4, 0.0, 0.2, 1)')),
        ])
    ]
})
export class CompetitorsComponent implements OnInit {
    displayedColumns: string[] = ['expand', 'name', 'headquarters', 'activeDrugs', 'pipelineDrugs', 'actions'];
    trialColumns: string[] = ['trialId', 'drugName', 'phase', 'indication', 'status', 'startDate'];
    dataSource: Competitor[] = [];
    loading = true;

    expandedElement: Competitor | null = null;
    trialsMap: Map<string, ClinicalTrial[]> = new Map();
    trialsLoading: Map<string, boolean> = new Map();

    constructor(
        public competitorService: CompetitorService,
        private zone: NgZone,
        private cdr: ChangeDetectorRef,
        private dialog: MatDialog,
        private snackBar: MatSnackBar,
        private authService: AuthService
    ) { }

    get isAdmin(): boolean {
        return this.authService.isAdmin;
    }

    ngOnInit() {
        this.loadCompetitors();
    }

    loadCompetitors() {
        this.loading = true;
        this.competitorService.getCompetitors().subscribe({
            next: (data) => {
                this.zone.run(() => {
                    this.dataSource = data;
                    this.loading = false;
                    this.cdr.detectChanges();
                });
            },
            error: (err) => {
                this.zone.run(() => {
                    console.error('CompetitorsComponent: Error', err);
                    this.loading = false;
                    this.cdr.detectChanges();
                });
            }
        });
    }

    toggleRow(element: Competitor) {
        if (this.expandedElement === element) {
            this.expandedElement = null;
        } else {
            this.expandedElement = element;
            if (!this.trialsMap.has(element.id)) {
                this.loadTrials(element.id);
            }
        }
    }

    loadTrials(competitorId: string) {
        this.trialsLoading.set(competitorId, true);
        this.competitorService.getTrials(competitorId).subscribe({
            next: (trials) => {
                this.trialsMap.set(competitorId, trials);
                this.trialsLoading.set(competitorId, false);
                this.cdr.detectChanges();
            },
            error: () => {
                this.trialsMap.set(competitorId, []);
                this.trialsLoading.set(competitorId, false);
                this.cdr.detectChanges();
            }
        });
    }

    openDialog(competitor?: Competitor): void {
        const dialogRef = this.dialog.open(CompetitorDialogComponent, {
            width: '500px',
            data: competitor || null
        });

        dialogRef.afterClosed().subscribe(result => {
            if (result) {
                if (competitor && competitor.id) {
                    this.competitorService.updateCompetitor(competitor.id, result).subscribe({
                        next: () => {
                            this.loadCompetitors();
                            this.snackBar.open('Competitor updated successfully', 'Close', { duration: 3000 });
                        },
                        error: (err) => {
                            if (err.status === 403) {
                                this.snackBar.open('You are not authorized to perform this operation.', 'Close', { duration: 5000 });
                            } else {
                                this.snackBar.open('Failed to update: ' + (err.error?.detail || err.message), 'Close', { duration: 5000 });
                            }
                        }
                    });
                } else {
                    this.competitorService.createCompetitor(result).subscribe({
                        next: () => {
                            this.loadCompetitors();
                            this.snackBar.open('Competitor created successfully', 'Close', { duration: 3000 });
                        },
                        error: (err) => {
                            if (err.status === 403) {
                                this.snackBar.open('You are not authorized to perform this operation.', 'Close', { duration: 5000 });
                            } else {
                                this.snackBar.open('Failed to create: ' + (err.error?.detail || err.message), 'Close', { duration: 5000 });
                            }
                        }
                    });
                }
            }
        });
    }

    deleteCompetitor(id: string): void {
        if (confirm('Are you sure you want to delete this competitor?')) {
            this.competitorService.deleteCompetitor(id).subscribe({
                next: () => {
                    this.loadCompetitors();
                    this.trialsMap.delete(id);
                    this.snackBar.open('Competitor and linked trials deleted', 'Close', { duration: 3000 });
                },
                error: (err) => {
                    if (err.status === 403) {
                        this.snackBar.open('You are not authorized to perform this operation.', 'Close', { duration: 5000 });
                    } else {
                        this.snackBar.open('Failed to delete: ' + (err.error?.detail || err.message), 'Close', { duration: 5000 });
                    }
                }
            });
        }
    }

    getPhaseColor(phase: string | undefined): string {
        if (!phase) return 'bg-gray-100 text-gray-600';
        const p = phase.toLowerCase();
        if (p.includes('3') || p.includes('iii')) return 'bg-purple-100 text-purple-800';
        if (p.includes('2') || p.includes('ii')) return 'bg-blue-100 text-blue-800';
        if (p.includes('1') || p.includes('i')) return 'bg-green-100 text-green-800';
        return 'bg-gray-100 text-gray-600';
    }

    getStatusColor(status: string | undefined): string {
        if (!status) return 'bg-gray-100 text-gray-600';
        const s = status.toLowerCase();
        if (s.includes('recruit')) return 'bg-green-100 text-green-800';
        if (s.includes('active') || s.includes('new')) return 'bg-blue-100 text-blue-800';
        if (s.includes('complet')) return 'bg-gray-100 text-gray-800';
        return 'bg-yellow-100 text-yellow-800';
    }
}
