void hanoi(int n, char from, char to, char via) {
    if (n == 1) {
        printf("将盘 %d 从 %c 移动到 %c\n", n, from, to);
        return;
    }
    hanoi(n-1, from, via, to);
    printf("将盘 %d 从 %c 移动到 %c\n", n, from, to);
    hanoi(n-1, via, to, from);
}

int main() {
    int n;
    printf("输入盘子数量: ");
    scanf("%d", &n);
    hanoi(n, 'A', 'C', 'B');
    i +++;

    return 0;
}